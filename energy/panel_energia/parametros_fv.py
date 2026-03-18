from __future__ import annotations

"""
PARÁMETROS DEL MÓDULO FV — FV Engine

Dominio: paneles / energía

Responsabilidad
---------------
Definir las características eléctricas y térmicas del
módulo fotovoltaico utilizadas por el motor DC.

Este modelo representa el comportamiento del panel en
condiciones nominales (referencia implícita).
"""

from dataclasses import dataclass


# ==========================================================
# PARÁMETROS DEL MÓDULO FV
# ==========================================================

@dataclass(frozen=True)
class ParametrosFV:
    """
    Parámetros físicos del módulo fotovoltaico.

    Este modelo es utilizado por:

        modelo_termico
        potencia_panel

    No incluye pérdidas, clima ni configuración del sistema.
    """

    # ------------------------------------------------------
    # POTENCIA
    # ------------------------------------------------------

    p_panel_w: float

    # ------------------------------------------------------
    # VOLTAJES
    # ------------------------------------------------------

    vmp_panel_v: float
    voc_panel_v: float

    # ------------------------------------------------------
    # CORRIENTES
    # ------------------------------------------------------

    imp_panel_a: float
    isc_panel_a: float

    # ------------------------------------------------------
    # COEFICIENTES TÉRMICOS
    # (en 1/°C, ej: -0.0035)
    # ------------------------------------------------------

    coef_potencia: float
    coef_vmp: float
    coef_voc: float

    # ------------------------------------------------------
    # PARÁMETRO TÉRMICO
    # ------------------------------------------------------

    noct_c: float
