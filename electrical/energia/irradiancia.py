# electrical/energia/irradiancia.py

from __future__ import annotations

"""
MODELO BASE DE IRRADIANCIA — FV Engine
======================================

Este módulo define el modelo climático simplificado del
dominio energético del sistema fotovoltaico.

Responsabilidad
----------------

Proveer información climática base para los motores energéticos.

Este módulo entrega:

• HSP promedio mensual
• número de días por mes
• perfil horario normalizado de irradiancia

NO realiza cálculos de generación FV.

El cálculo energético ocurre en:

    generacion_bruta.py
    perdidas_fisicas.py
    modelo_energetico_inversor.py


Concepto físico
----------------

HSP (Horas Sol Pico)

Representa la energía solar diaria equivalente a una irradiancia
de 1000 W/m² durante cierto número de horas.

Ejemplo:

    HSP = 5.0

equivale a:

    5 kWh/m²/día


Uso dentro del motor FV
-----------------------

    irradiancia
        ↓
    generacion_bruta
        ↓
    perdidas
        ↓
    modelo inversor
"""

from typing import List
import math


# ==========================================================
# DÍAS POR MES
# ==========================================================

DIAS_MES: List[int] = [
    31,  # Enero
    28,  # Febrero
    31,  # Marzo
    30,  # Abril
    31,  # Mayo
    30,  # Junio
    31,  # Julio
    31,  # Agosto
    30,  # Septiembre
    31,  # Octubre
    30,  # Noviembre
    31,  # Diciembre
]


# ==========================================================
# HSP PROMEDIO MENSUAL
# ==========================================================

def hsp_12m_base() -> List[float]:
    """
    Retorna el perfil mensual promedio de HSP.

    Unidad:
        kWh/m²/día

    Perfil típico para región tropical.
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
# HSP PROMEDIO ANUAL
# ==========================================================

def hsp_anual() -> float:
    """
    Calcula el HSP promedio anual.

    Retorna:
        float (kWh/m²/día)
    """

    valores = hsp_12m_base()

    return sum(valores) / len(valores)


# ==========================================================
# PERFIL HORARIO DE IRRADIANCIA
# ==========================================================

def hsp_a_perfil_horario(hsp_dia: float) -> List[float]:
    """
    Convierte un valor de HSP diario en un perfil horario.

    La forma de la curva es sinusoidal para aproximar
    el comportamiento diario de irradiancia solar.

    Retorna:
        lista de 24 valores (kWh/m² por hora)

    Propiedad importante:

        sum(perfil) == hsp_dia
    """

    curva = []

    for hora in range(24):

        # irradiancia entre 6 AM y 6 PM

        if 6 <= hora <= 18:

            angulo = (hora - 6) / 12 * math.pi
            valor = math.sin(angulo)

        else:

            valor = 0.0

        curva.append(valor)

    suma = sum(curva)

    if suma == 0:
        return [0.0] * 24

    factor = hsp_dia / suma

    perfil = [round(v * factor, 6) for v in curva]

    return perfil


# ==========================================================
# PERFILES HORARIOS DE LOS 12 MESES
# ==========================================================

def perfiles_horarios_12m() -> List[List[float]]:
    """
    Genera el perfil horario de irradiancia para cada mes.

    Retorna:

        lista de 12 elementos

    cada elemento contiene:

        24 valores horarios
    """

    hsp = hsp_12m_base()

    perfiles: List[List[float]] = []

    for valor in hsp:

        perfil = hsp_a_perfil_horario(valor)

        perfiles.append(perfil)

    return perfiles


# ==========================================================
# SALIDAS DEL MÓDULO
# ==========================================================

"""
Este módulo exporta:

DIAS_MES
    lista con número de días por mes

hsp_12m_base()
    HSP promedio mensual

hsp_anual()
    HSP promedio anual

hsp_a_perfil_horario()
    perfil horario (24h)

perfiles_horarios_12m()
    perfiles horarios de los 12 meses
"""
