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
    # 2. PANELES / STRINGS
    # ======================================================
    print("\n[2] EJECUTANDO PANEL / STRINGS")

    resultado_paneles = deps.paneles.ejecutar(datos, sizing)

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
    # 3. ELECTRICAL (NEC)
    # ======================================================
    print("\n[3] CALCULOS ELECTRICOS")

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
            resultado_electrico = None  # ⚠ no romper flujo

        if resultado_electrico is None:
            print("⚠ Electrical devolvió None")

        elif getattr(resultado_electrico, "ok", True) is False:
            print("⚠ Electrical con errores, se continúa flujo")

    # ======================================================
    # 4. ENERGÍA
    # ======================================================
    print("\n[4] EJECUTANDO ENERGIA")

    print("DEBUG INPUT ENERGIA:")
    print(" - sizing:", sizing)
    print(" - paneles:", resultado_paneles)

    try:
        energia = deps.energia.ejecutar(
            datos,
            sizing,
            resultado_paneles,
        )
    except Exception as e:
        print("🔥 ERROR ENERGIA:", str(e))
        energia = None

    if energia is None:
        print("⚠ Energía devolvió None")

    elif getattr(energia, "ok", True) is False:
        print("⚠ Energía con errores")

    # ======================================================
    # 5. FINANZAS (OPCIONAL)
    # ======================================================
    print("\n[5] EJECUTANDO FINANZAS")

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
