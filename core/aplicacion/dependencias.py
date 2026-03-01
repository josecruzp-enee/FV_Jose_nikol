from core.servicios.sizing import calcular_sizing_unificado
from core.servicios.finanzas import ejecutar_finanzas

from electrical.paneles.orquestador_paneles import ejecutar_paneles_desde_sizing
from electrical.energia.orquestador_energia import ejecutar_motor_energia
from electrical.energia.contrato import EnergiaInput
from electrical.nec.orquestador_nec import ejecutar_nec

from .puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
    PuertoFinanzas,
)

from .orquestador_estudio import DependenciasEstudio


# -----------------------------
# ADAPTADORES
# -----------------------------

class SizingAdapter(PuertoSizing):
    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


class PanelesAdapter(PuertoPaneles):
    def ejecutar(self, datos, sizing):
        return ejecutar_paneles_desde_sizing(datos, sizing)


class EnergiaAdapter(PuertoEnergia):
    def ejecutar(self, datos, sizing, strings):

        # Construimos el contrato que espera el motor de energía
        inp = EnergiaInput(
            datos=datos,
            sizing=sizing,
            strings=strings,
        )

        return ejecutar_motor_energia(inp)


class NECAdapter(PuertoNEC):
    def ejecutar(self, datos, sizing, strings):
        return ejecutar_nec(datos, sizing, strings)


class FinanzasAdapter(PuertoFinanzas):
    def ejecutar(self, datos, sizing, energia):
        return ejecutar_finanzas(
            datos=datos,
            sizing=sizing,
            energia=energia,
        )


# -----------------------------
# FACTORY DE DEPENDENCIAS
# -----------------------------

def construir_dependencias() -> DependenciasEstudio:
    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=NECAdapter(),
        finanzas=FinanzasAdapter(),
    )
