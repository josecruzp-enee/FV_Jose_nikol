# electrical/ingenieria_nec_2023.py
"""
SHIM LEGACY — NO lógica aquí.

Compatibilidad:
- Mantiene el símbolo histórico `calcular_paquete_electrico_nec(datos)`
- Ahora delega al nuevo orquestador `electrical.paquete_nec.armar_paquete_nec`

Regla dura:
- Este archivo NO debe contener cálculos.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping

from electrical.paquete_nec import armar_paquete_nec


def calcular_paquete_electrico_nec(datos: Mapping[str, Any]) -> Dict[str, Any]:
    # Delegación directa al orquestador nuevo
    return armar_paquete_nec(datos)


__all__ = ["calcular_paquete_electrico_nec"]
