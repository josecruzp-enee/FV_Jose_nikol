# electrical/energia/irradiancia.py

"""
Modelo de irradiancia base del sistema FV.

Este módulo provee el perfil de HSP promedio diario por mes
para Honduras.

NO realiza cálculos de generación.
NO depende de UI ni de core.

Es únicamente el origen climático del dominio energía.
"""

from __future__ import annotations
from typing import List


# ==========================================================
# CONSTANTES CLIMÁTICAS
# ==========================================================

DIAS_MES: List[int] = [
    31,  # Ene
    28,  # Feb
    31,  # Mar
    30,  # Abr
    31,  # May
    30,  # Jun
    31,  # Jul
    31,  # Ago
    30,  # Sep
    31,  # Oct
    30,  # Nov
    31,  # Dic
]


# ==========================================================
# PERFIL HSP BASE
# ==========================================================

def hsp_12m_base() -> List[float]:
    """
    Perfil mensual oficial de HSP promedio diario.

    Unidad:
        kWh/m²/día

    Fuente:
        Modelo climático promedio Honduras.

    Retorna:
        Lista de 12 valores correspondientes a
        Enero–Diciembre.
    """

    return [
        5.1,  # Ene
        5.4,  # Feb
        5.8,  # Mar
        5.6,  # Abr
        5.0,  # May
        4.5,  # Jun
        4.3,  # Jul
        4.4,  # Ago
        4.1,  # Sep
        4.0,  # Oct
        4.4,  # Nov
        4.7,  # Dic
    ]


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# DIAS_MES
#
# Tipo:
# list[int]
#
# Descripción:
# Número de días de cada mes (Ene–Dic)
#
# Consumido por:
# energia.generacion_bruta
#
#
# hsp_12m_base()
#
# Tipo:
# list[float]
#
# Descripción:
# HSP promedio diario mensual (kWh/m²/día)
#
# Consumido por:
# energia.generacion_bruta
#
# ==========================================================
