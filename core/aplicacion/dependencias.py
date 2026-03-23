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

# 🔥 IMPORTS REALES
from core.servicios.sizing import calcular_sizing_unificado
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.orquestador_electrical import ejecutar_electrical
from energy.orquestador_energia import ejecutar_motor_energia as ejecutar_energia
from core.servicios.finanzas import ejecutar_finanzas


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
# ADAPTERS
# ==========================================================

class SizingAdapter:
    def ejecutar(self, datos):
        resultado = calcular_sizing_unificado(datos)

        if resultado is None:
            raise ValueError("Sizing devolvió None desde servicio")

        return resultado


class PanelesAdapter:
    def ejecutar(self, datos, sizing):
        resultado = ejecutar_paneles(datos=datos, sizing=sizing)

        if resultado is None:
            raise ValueError("Paneles devolvió None")

        return resultado


class ElectricalAdapter:
    def ejecutar(self, datos, paneles):
        resultado = ejecutar_electrical(datos=datos, paneles=paneles)

        if resultado is None:
            raise ValueError("Electrical devolvió None")

        return resultado


class EnergiaAdapter:
    def ejecutar(self, datos, sizing, paneles):
        # ⚠️ Aquí probablemente luego ajustarás contrato
        resultado = ejecutar_energia(datos, sizing, paneles)

        if resultado is None:
            raise ValueError("Energía devolvió None")

        return resultado


class FinanzasAdapter:
    def ejecutar(self, datos, sizing, energia):
        resultado = ejecutar_finanzas(datos, sizing, energia)

        if resultado is None:
            raise ValueError("Finanzas devolvió None")

        return resultado


# ==========================================================
# FACTORY
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
# ORQUESTADOR (🔥 CORREGIDO)
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

        if getattr(energia, "ok", True) is False:
            return ResultadoProyecto(
                sizing=sizing,
                strings=resultado_paneles,
                energia=energia,
                nec=resultado_electrico,
                financiero=None,
            )

        # ------------------------------------------------------
        # 5. FINANZAS
        # ------------------------------------------------------
        print("\n[5] EJECUTANDO FINANZAS")

        financiero = None

        if deps.finanzas:
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

    except Exception:

        import traceback

        print("\n🔥 ERROR REAL EN ORQUESTADOR 🔥")
        print(traceback.format_exc())

        # 🔥 NO ocultamos el error
        raise
