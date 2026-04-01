from __future__ import annotations

from typing import Protocol

# ==========================================================
# DOMINIO (CONTRATO FUERTE)
# ==========================================================

from core.dominio.contrato import (
    Datosproyecto,
    ResultadoSizing,
    ResultadoFinanciero,
)

from electrical.paneles.resultado_paneles import ResultadoPaneles
from electrical.resultado_electrical import ResultadoElectrico
from energy.resultado_energia import EnergiaResultado

from electrical.paneles.entrada_panel import EntradaPaneles


# ==========================================================
# SIZING
# ==========================================================

class PuertoSizing(Protocol):
    def ejecutar(self, datos: Datosproyecto) -> ResultadoSizing:
        ...


# ==========================================================
# PANELES / STRINGS
# ==========================================================

class PuertoPaneles(Protocol):
    def ejecutar(self, entrada: EntradaPaneles) -> ResultadoPaneles:
        ...


# ==========================================================
# ENERGÍA
# ==========================================================

class PuertoEnergia(Protocol):
    def ejecutar(
        self,
        datos: Datosproyecto,
        sizing: ResultadoSizing,
        paneles: ResultadoPaneles,
    ) -> EnergiaResultado:
        ...


# ==========================================================
# ELECTRICAL
# ==========================================================

class PuertoElectrical(Protocol):
    def ejecutar(
        self,
        *,
        datos: Datosproyecto,
        paneles: ResultadoPaneles,
        sizing: ResultadoSizing,
    ) -> ResultadoElectrico:
        ...


# ==========================================================
# FINANZAS
# ==========================================================

class PuertoFinanzas(Protocol):
    def ejecutar(
        self,
        datos: Datosproyecto,
        sizing: ResultadoSizing,
        energia: EnergiaResultado,
    ) -> ResultadoFinanciero:
        ...
