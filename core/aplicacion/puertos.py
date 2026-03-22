from typing import Protocol

from core.dominio.contrato import ResultadoSizing
from electrical.paneles.resultado_paneles import ResultadoPaneles
from energy.contrato import EnergiaResultado


class PuertoSizing(Protocol):
    def ejecutar(self, datos) -> ResultadoSizing: ...


class PuertoPaneles(Protocol):
    def ejecutar(self, datos, sizing: ResultadoSizing) -> ResultadoPaneles: ...


class PuertoNEC(Protocol):
    def ejecutar(self, datos, sizing: ResultadoSizing, paneles: ResultadoPaneles):
        ...


class PuertoEnergia(Protocol):
    def ejecutar(self, datos, sizing: ResultadoSizing, paneles: ResultadoPaneles) -> EnergiaResultado: ...


class PuertoFinanzas(Protocol):
    def ejecutar(self, datos, sizing: ResultadoSizing, energia: EnergiaResultado):
        ...
