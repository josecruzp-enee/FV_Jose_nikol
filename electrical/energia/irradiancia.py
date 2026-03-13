# electrical/energia/irradiancia.py

"""
Modelo de irradiancia base del sistema FV.

Este módulo provee:

• HSP promedio mensual
• días por mes
• conversión HSP → perfil horario (24h)

NO realiza cálculos de generación FV.
Es únicamente el origen climático del dominio energía.
"""

from __future__ import annotations
from typing import List
import math


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
    Perfil mensual promedio de HSP.

    Unidad:
        kWh/m²/día
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
# CONVERSIÓN HSP → PERFIL HORARIO
# ==========================================================

def hsp_a_perfil_horario(hsp_dia: float) -> List[float]:
    """
    Convierte HSP diario a perfil horario de irradiancia.

    La suma de las 24 horas será igual al HSP.

    Retorna:
        24 valores (kWh/m² por hora)
    """

    curva = []

    for h in range(24):

        if 6 <= h <= 18:

            angulo = (h - 6) / 12 * math.pi
            valor = math.sin(angulo)

        else:

            valor = 0

        curva.append(valor)

    suma = sum(curva)

    if suma == 0:
        return [0] * 24

    factor = hsp_dia / suma

    perfil = [round(v * factor, 4) for v in curva]

    return perfil


# ==========================================================
# PERFIL HORARIO POR MES
# ==========================================================

def perfiles_horarios_12m() -> List[List[float]]:
    """
    Genera perfil horario (24h) para cada mes.

    Retorna:
        Lista de 12 meses × 24 horas
    """

    hsp = hsp_12m_base()

    perfiles = []

    for valor in hsp:

        perfil = hsp_a_perfil_horario(valor)

        perfiles.append(perfil)

    return perfiles


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# DIAS_MES
#
# list[int]
#
# Número de días por mes
#
#
# hsp_12m_base()
#
# list[float]
#
# HSP promedio diario mensual
#
#
# hsp_a_perfil_horario()
#
# list[float]
#
# Convierte HSP a perfil horario (24h)
#
#
# perfiles_horarios_12m()
#
# list[list[float]]
#
# Perfiles horarios de irradiancia para los 12 meses
#
# ==========================================================
