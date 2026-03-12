"""
Modelos del dominio eléctrico FV.

FRONTERA DEL PAQUETE
====================

Exporta los contratos de datos usados por el motor eléctrico.

Modelos disponibles:
    PanelSpec
    InversorSpec

Consumido por:
    electrical.paneles
    electrical.inversor
    electrical.corrientes
    electrical.protecciones
    electrical.conductores
    electrical.nec
"""

from .paneles import PanelSpec
from .inversor import InversorSpec

__all__ = [
    "PanelSpec",
    "InversorSpec",
]
