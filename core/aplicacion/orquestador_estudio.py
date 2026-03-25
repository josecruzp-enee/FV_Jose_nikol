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

# 🔥 NUEVO
from electrical.paneles.entrada_panel import EntradaPaneles


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
    # 2. CONSTRUIR ENTRADA PANEL (🔥 CORREGIDO)
    # ======================================================
    print("\n[2] CONSTRUYENDO ENTRADA PANELES")

    from electrical.catalogos.catalogos_yaml import get_panel

    # 🔥 obtener panel desde UI (equipos)
    equipos = getattr(datos, "equipos", {}) or {}
    panel_id = equipos.get("panel_id")

    if not panel_id:
        raise ValueError("No se definió panel_id en datos.equipos")

    panel = get_panel(panel_id)

    print("DEBUG PANEL:")
    print(" - panel_id:", panel_id)
    print(" - pmax_w:", getattr(panel, "pmax_w", None))

    entrada_paneles = EntradaPaneles(
        panel=panel,
        inversor=sizing.inversor,
        n_inversores=sizing.n_inversores,
        n_paneles_total=getattr(sizing, "n_paneles", None),
        t_min_c=datos.clima.t_min,
        t_oper_c=getattr(datos.clima, "t_oper", 55),
    )

    print("DEBUG ENTRADA PANELES:")
    print(" - inversor:", entrada_paneles.inversor)
    print(" - n_inversores:", entrada_paneles.n_inversores)

    # ======================================================
    # 3. PANELES / STRINGS
    # ======================================================
    print("\n[3] EJECUTANDO PANEL / STRINGS")

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

            print("DEBUG ELECTRICAL:", resultado_electrico)

        except Exception as e:
            print("🔥 ERROR ELECTRICAL:", str(e))
            resultado_electrico = None

        if resultado_electrico is None:
            print("⚠ Electrical devolvió None")

        elif getattr(resultado_electrico, "ok", True) is False:
            print("⚠ Electrical con errores, se continúa flujo")

    # ======================================================
    # 5. ENERGÍA
    # ======================================================
    print("\n[5] EJECUTANDO ENERGIA")

    print("DEBUG INPUT ENERGIA:")
    print(" - sizing:", sizing)
    print(" - paneles:", resultado_paneles)

    energia = deps.energia.ejecutar(
        datos,
        sizing,
        resultado_paneles,
    )

    if energia is None:
        raise ValueError("Energía devolvió None")

    if not getattr(energia, "ok", True):
        raise ValueError(f"Energía inválida: {energia.errores}")

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
