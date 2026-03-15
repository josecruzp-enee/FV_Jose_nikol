from __future__ import annotations

"""
CONTRATO DE ENTRADA — DOMINIO SOLAR

Este módulo define la estructura de datos que recibe el
dominio solar para calcular:

• posición del sol
• irradiancia en plano del arreglo (POA)

Este módulo NO contiene lógica de cálculo.

Consumido por:
    solar.orquestador_solar
"""

from dataclasses import dataclass
from datetime import datetime


# ==========================================================
# ENTRADA DEL DOMINIO SOLAR
# ==========================================================

@dataclass
class EntradaSolar:
    """
    Parámetros requeridos para los cálculos solares.
    """

    # ------------------------------------------------------
    # Ubicación
    # ------------------------------------------------------

    lat: float
    lon: float

    # ------------------------------------------------------
    # Tiempo
    # ------------------------------------------------------

    fecha_hora: datetime

    # ------------------------------------------------------
    # Radiación disponible
    # ------------------------------------------------------

    ghi_wm2: float

    # ------------------------------------------------------
    # Geometría del arreglo FV
    # ------------------------------------------------------

    tilt_deg: float
    azimuth_panel_deg: float
