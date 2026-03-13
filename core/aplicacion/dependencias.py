from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

from core.servicios.sizing import calcular_sizing_unificado
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.energia.orquestador_energia import ejecutar_motor_energia
from electrical.nec.orquestador_nec import ejecutar_nec
from core.servicios.finanzas import ejecutar_finanzas


class SizingAdapter:
    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


class PanelesAdapter:
    def ejecutar(self, datos, sizing):
        # Si tu orquestador de paneles espera otra firma, ajústalo aquí
        return ejecutar_paneles(datos, sizing)


class EnergiaAdapter:
    def ejecutar(self, datos, sizing, strings):
        return ejecutar_motor_energia(datos, sizing, strings)


class NECAdapter:
    def ejecutar(self, datos, sizing, strings):
        # Ajuste importante: si tu ejecutar_nec espera (entrada_nec, sizing, strings)
        # entonces aquí deberías construir 'entrada_nec'. Si tu versión ya acepta
        # (datos, sizing, strings), esto funciona tal cual.
        return ejecutar_nec(datos, sizing, strings)


class FinanzasAdapter:
    def ejecutar(self, datos, sizing, energia):
        return ejecutar_finanzas(datos, sizing, energia)


def construir_dependencias():
    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=NECAdapter(),
        finanzas=FinanzasAdapter(),
    )
