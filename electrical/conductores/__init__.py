"""
Paquete conductores — FV Engine.

Subdominio de dimensionamiento eléctrico.

API pública estable:
- calcular_corrientes → obtiene corrientes de diseño DC/AC
- tramo_conductor     → dimensiona conductor (NEC + VD)

Nota:
Las funciones físicas internas (modelo_tramo, tablas, NEC)
NO forman parte de la API pública.
"""

from __future__ import annotations

from .corrientes import calcular_corrientes
from .calculo_conductores import tramo_conductor

__all__ = [
    "calcular_corrientes",
    "tramo_conductor",
]
