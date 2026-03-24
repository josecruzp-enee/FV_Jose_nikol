from typing import Protocol, Any

from core.dominio.contrato import ResultadoSizing
from electrical.paneles.resultado_paneles import ResultadoPaneles
from electrical.resultado_electrical import ResultadoElectrico
from energy.contrato import EnergiaResultado


# ==========================================================
# SIZING
# ==========================================================

class PuertoSizing(Protocol):
    def ejecutar(self, datos: Any) -> ResultadoSizing: ...


# ==========================================================
# PANELES
# ==========================================================

class PuertoPaneles(Protocol):
    def ejecutar(self, datos: Any, sizing: ResultadoSizing) -> ResultadoPaneles: ...


# ==========================================================
# ELECTRICAL (NEC)
# ==========================================================

class PuertoNEC(Protocol):
    def ejecutar(
        self,
        *,
        datos: Any,
        paneles: ResultadoPaneles,
        sizing: ResultadoSizing,  
    ) -> ResultadoElectrico: ...


# ==========================================================
# ENERGÍA
# ==========================================================

class PuertoEnergia(Protocol):
    def ejecutar(
        self,
        datos: Any,
        sizing: ResultadoSizing,
        paneles: ResultadoPaneles
    ) -> EnergiaResultado: ...


# ==========================================================
# FINANZAS
# ==========================================================

class PuertoFinanzas(Protocol):
    def ejecutar(
        self,
        datos: Any,
        sizing: ResultadoSizing,
        energia: EnergiaResultado
    ): ...
