"""
Paquete conductores — FV Engine.

API pública estable del subdominio conductores.

Expone únicamente:
- calcular_corrientes      → obtiene corrientes DC/AC de diseño
- tramo_conductor          → dimensiona un tramo individual (NEC + VD)
- dimensionar_tramos_fv    → orquesta tramos FV típicos
"""

from __future__ import annotations

from .corrientes import calcular_corrientes
from .calculo_conductores import (
    tramo_conductor,
    dimensionar_tramos_fv,
)

__all__ = [
    "calcular_corrientes",
    "tramo_conductor",
    "dimensionar_tramos_fv",
]
