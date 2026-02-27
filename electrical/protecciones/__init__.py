"""
Paquete protecciones — FV Engine.

API pública estable del subdominio protecciones.

Expone únicamente:
- dimensionar_protecciones_fv → dimensionamiento OCPD FV (AC/DC)
"""

from __future__ import annotations

from electrical.protecciones import armar_ocpd

__all__ = ["dimensionar_protecciones_fv"]
