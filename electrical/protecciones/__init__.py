"""
Paquete protecciones — FV Engine.

API pública estable del subdominio protecciones.

Expone únicamente:
- dimensionar_protecciones_fv → dimensionamiento OCPD FV (AC/DC)
"""

from __future__ import annotations

from .protecciones import dimensionar_protecciones_fv

__all__ = ["dimensionar_protecciones_fv"]
