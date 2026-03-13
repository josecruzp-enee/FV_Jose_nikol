from __future__ import annotations

"""
MODELO CLIMÁTICO — FV Engine

Responsabilidad
---------------
Definir la estructura de datos climáticos horarios
utilizados por el motor energético.

Este módulo NO genera datos climáticos.

Los datos pueden provenir de:

• PVGIS
• TMY
• clima sintético
"""

from dataclasses import dataclass


# ==========================================================
# ESTRUCTURA DE DATOS CLIMÁTICOS
# ==========================================================

@dataclass
class ClimaHora:
    """
    Representa las condiciones climáticas de una hora.
    """

    ghi_wm2: float
    temp_amb_c: float
