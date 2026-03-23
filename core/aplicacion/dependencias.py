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

# 🔥 IMPORTS REALES DE TU PROYECTO
from core.servicios.sizing import calcular_sizing_unificado
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.orquestador_electrical import ejecutar_electrical
from energy.orquestador_energia import ejecutar_energia
from core.finanzas.orquestador_finanzas import ejecutar_finanzas


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
# ADAPTERS INLINE (🔥 SIN carpeta adapters)
# ==========================================================

class SizingAdapter:
    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


class PanelesAdapter:
    def ejecutar(self, datos, sizing):
        return ejecutar_paneles(
            datos=datos,
            sizing=sizing,
        )


class ElectricalAdapter:
    def ejecutar(self, datos, paneles):
        return ejecutar_electrical(
            datos=datos,
            paneles=paneles,
        )


class EnergiaAdapter:
    def ejecutar(self, datos, sizing, paneles):
        return ejecutar_energia(
            datos,
            sizing,
            paneles,
        )


class FinanzasAdapter:
    def ejecutar(self, datos, sizing, energia):
        return ejecutar_finanzas(
            datos,
            sizing,
            energia,
        )


# ==========================================================
# FACTORY (🔥 ESTE ERA EL FALTANTE)
# ==========================================================

def construir_dependencias() -> DependenciasEstudio:
    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=ElectricalAdapter(),
        finanzas=FinanzasAdapter(),
    )


# ==========================================================
# ORQUESTADOR
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
        # 3. ELECTRICAL
        # ------------------------------------------------------

        print("\n[3] CALCULOS ELECTRICOS")

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

        else:
            resultado_electrico = None

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

        print("\n❌ ERROR EN ORQUESTADOR:", str(e))

        return ResultadoProyecto(
            sizing=None,
            strings=None,
            energia=None,
            nec=None,
            financiero=None,
        )
