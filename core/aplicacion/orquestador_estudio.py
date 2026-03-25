from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.dominio.contrato import ResultadoProyecto

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
    PuertoFinanzas,
)

from electrical.paneles.entrada_panel import EntradaPaneles
from core.aplicacion.multizona import ejecutar_multizona


# ==========================================================
# DEPENDENCIAS
# ==========================================================
@dataclass
class DependenciasEstudio:
    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    nec: Optional[PuertoNEC] = None
    finanzas: Optional[PuertoFinanzas] = None


# ==========================================================
# ORQUESTADOR
# ==========================================================
def ejecutar_estudio(
    datos: Any,
    deps: DependenciasEstudio,
) -> ResultadoProyecto:

    print("\n==============================")
    print("FV ENGINE — INICIO ESTUDIO")
    print("==============================")

    # ======================================================
    # 1. SIZING
    # ======================================================
    print("\n[1] EJECUTANDO SIZING")

    sizing = deps.sizing.ejecutar(datos)

    if sizing is None:
        raise ValueError("Sizing devolvió None")

    if getattr(sizing, "ok", True) is False:
        return ResultadoProyecto(
            sizing=sizing,
            strings=None,
            energia=None,
            nec=None,
            financiero=None,
        )

    # ======================================================
    # 2. CONSTRUIR ENTRADA PANELES
    # ======================================================
    print("\n[2] CONSTRUYENDO ENTRADA PANELES")

    from electrical.catalogos.catalogos_yaml import get_panel

    equipos = getattr(datos, "equipos", {}) or {}
    panel_id = equipos.get("panel_id")

    print("DEBUG panel_id:", panel_id)

    if not panel_id:
        raise ValueError("No se definió panel_id en datos.equipos")

    panel = get_panel(panel_id)

    # 🔥 FIX CRÍTICO
    if panel is None:
        raise ValueError(f"Panel no encontrado en catálogo: {panel_id}")

    sf = getattr(datos, "sistema_fv", {}) or {}

    entrada_paneles = EntradaPaneles(
        panel=panel,
        inversor=sizing.inversor,
        n_inversores=sizing.n_inversores,
        n_paneles_total=getattr(sizing, "n_paneles", None),
    )

    # ======================================================
    # 3. PANELES / STRINGS (MULTIZONA)
    # ======================================================
    print("\n[3] EJECUTANDO PANEL / STRINGS")

    zonas = sf.get("zonas") if isinstance(sf, dict) else None

    if zonas:
        print("🔥 MODO MULTIZONA ACTIVADO")

        entradas_zonas = []

        total_paneles = getattr(sizing, "n_paneles", None)
        if not total_paneles:
            raise ValueError("No se pudo obtener n_paneles desde sizing")

        n_zonas = len(zonas)
        base = total_paneles // n_zonas
        resto = total_paneles % n_zonas

        for i, z in enumerate(zonas):

            n_paneles_zona = z.get("n_paneles")

            # 🔥 MODO MANUAL
            if not n_paneles_zona:
                if i < resto:
                    n_paneles_zona = base + 1
                else:
                    n_paneles_zona = base

            print(f"Zona {i} → paneles:", n_paneles_zona)

            entrada_z = EntradaPaneles(
                panel=panel,
                inversor=sizing.inversor,
                n_inversores=sizing.n_inversores,
                n_paneles_total=n_paneles_zona,
            )

            entradas_zonas.append(entrada_z)

        resultado_paneles = ejecutar_multizona(entradas_zonas)

    else:
        resultado_paneles = deps.paneles.ejecutar(entrada_paneles)

    if resultado_paneles is None:
        raise ValueError("Paneles devolvió None")

    if not resultado_paneles.ok:
        return ResultadoProyecto(
            sizing=sizing,
            strings=resultado_paneles,
            energia=None,
            nec=None,
            financiero=None,
        )

    # ======================================================
    # 4. ELECTRICAL (NEC)
    # ======================================================
    print("\n[4] CALCULOS ELECTRICOS")

    resultado_electrico = None

    if deps.nec:
        try:
            resultado_electrico = deps.nec.ejecutar(
                datos=datos,
                paneles=resultado_paneles,
                sizing=sizing,
            )
        except Exception as e:
            print("🔥 ERROR ELECTRICAL:", str(e))
            resultado_electrico = None

    # ======================================================
    # 5. ENERGÍA
    # ======================================================
    print("\n[5] EJECUTANDO ENERGIA")

    energia = deps.energia.ejecutar(
        datos,
        sizing,
        resultado_paneles,
    )

    if energia is None:
        raise ValueError("Energía devolvió None")

    # ======================================================
    # 6. FINANZAS
    # ======================================================
    print("\n[6] EJECUTANDO FINANZAS")

    financiero = None

    if deps.finanzas and energia is not None:
        try:
            financiero = deps.finanzas.ejecutar(
                datos,
                sizing,
                energia,
            )
        except Exception as e:
            print("🔥 ERROR FINANZAS:", str(e))
            financiero = None

    # ======================================================
    # RESULTADO FINAL
    # ======================================================
    resultado = ResultadoProyecto(
        sizing=sizing,
        strings=resultado_paneles,
        energia=energia,
        nec=resultado_electrico,
        financiero=financiero,
    )

    print("\n==============================")
    print("FV ENGINE — FIN ESTUDIO")
    print("==============================")

    return resultado
