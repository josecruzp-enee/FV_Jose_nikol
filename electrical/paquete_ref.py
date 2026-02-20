"""Compatibilidad legacy para import histórico `electrical.paquete_ref`.

Mantiene compat con código desplegado que aún importa:
    from electrical.paquete_ref import calcular_paquete_electrico_ref
"""

from __future__ import annotations

from electrical.paquete_electrico import calcular_paquete_electrico_ref

__all__ = ["calcular_paquete_electrico_ref"]
