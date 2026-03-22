from typing import Protocol

from core.dominio.contrato import ResultadoSizing
from electrical.paneles.resultado_paneles import ResultadoPaneles
from electrical.resultado_electrico import ResultadoElectrico
from energy.contrato import EnergiaResultado


# ==========================================================
# SIZING
# ==========================================================

class PuertoSizing(Protocol):
    def ejecutar(self, datos) -> ResultadoSizing: ...


# ==========================================================
# PANELES
# ==========================================================

class PuertoPaneles(Protocol):
    def ejecutar(self, datos, sizing: ResultadoSizing) -> ResultadoPaneles: ...


# ==========================================================
# ELECTRICAL (NEC)
# ==========================================================

class PuertoNEC(Protocol):
    def ejecutar(self, *, datos, paneles: ResultadoPaneles) -> ResultadoElectrico:
        ...


# ==========================================================
# ENERGÍA
# ==========================================================

class PuertoEnergia(Protocol):
    def ejecutar(self, datos, sizing: ResultadoSizing, paneles: ResultadoPaneles) -> EnergiaResultado:
        ...


# ==========================================================
# FINANZAS
# ==========================================================

class PuertoFinanzas(Protocol):
    def ejecutar(self, datos, sizing: ResultadoSizing, energia: EnergiaResultado):
        ...
