"""Shim de compatibilidad para import legacy ``electrical.paquete_ref``."""

from .paquete_electrico import calcular_paquete_electrico_ref

__all__ = ["calcular_paquete_electrico_ref"]
