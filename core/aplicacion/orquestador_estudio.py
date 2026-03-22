from __future__ import annotations

from dataclasses import dataclass, asdict
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
    finanzas: PuertoFinanzas = None


# ==========================================================
# ORQUESTADOR LIMPIO
# ==========================================================

def ejecutar_estudio(
    datos: Any,
    deps: DependenciasEstudio,
):

    print("\n==============================")
    print("FV ENGINE — INICIO ESTUDIO")
    print("==============================")

    try:

        # ------------------------------------------------------
        # 1. SIZING
        # ------------------------------------------------------

        print("\n[1] EJECUTANDO SIZING")

        sizing = deps.sizing.ejecutar(datos)

        if getattr(sizing, "ok", True) is False:
            return ResultadoProyecto(
                sizing=sizing,
                strings=None,
                energia=None,
                nec=None,
                financiero=None,
            )

        # ------------------------------------------------------
        # 2. PANELES
        # ------------------------------------------------------

        print("\n[2] EJECUTANDO PANEL / STRINGS")

        resultado_paneles = deps.paneles.ejecutar(datos, sizing)

        if not resultado_paneles.ok:
            return ResultadoProyecto(
                sizing=sizing,
                strings=resultado_paneles,
                energia=None,
                nec=None,
                financiero=None,
            )

        # ------------------------------------------------------
        # 3. ELECTRICAL (CAJA NEGRA)
        # ------------------------------------------------------

        print("\n[3] CALCULOS ELECTRICOS")

        resultado_electrico = None

        if deps.nec:
            resultado_electrico = deps.nec.ejecutar(
                datos=datos,
                paneles=resultado_paneles,
            )

            if not resultado_electrico.ok:
                return ResultadoProyecto(
                    sizing=sizing,
                    strings=resultado_paneles,
                    energia=None,
                    nec=resultado_electrico,
                    financiero=None,
                )

        # ------------------------------------------------------
        # 4. ENERGÍA
        # ------------------------------------------------------

        print("\n[4] EJECUTANDO ENERGIA")

        energia = deps.energia.ejecutar(
            datos,
            sizing,
            resultado_paneles,
        )

        # ------------------------------------------------------
        # 5. FINANZAS
        # ------------------------------------------------------

        print("\n[5] EJECUTANDO FINANZAS")

        financiero = deps.finanzas.ejecutar(
            datos,
            sizing,
            energia,
        )

        # ------------------------------------------------------
        # RESULTADO FINAL
        # ------------------------------------------------------

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

    except Exception as e:

        return ResultadoProyecto(
            sizing=None,
            strings=None,
            energia=None,
            nec=None,
            financiero=None,
        )
