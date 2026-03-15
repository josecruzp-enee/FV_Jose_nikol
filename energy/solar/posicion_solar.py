"""
POSICIÓN SOLAR — FV Engine

Dominio: solar

Responsabilidad
----------------
Calcular la posición del sol para una fecha y ubicación geográfica.

Este módulo implementa un modelo astronómico simplificado
adecuado para simulación energética de sistemas fotovoltaicos.

Entradas
--------
SolarInput

Salidas
-------
SolarPosition
"""

from dataclasses import dataclass
from datetime import datetime
from math import sin, cos, asin, acos, radians, degrees


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass
class SolarInput:
    """
    Parámetros de entrada para cálculo de posición solar
    """

    latitud_deg: float
    longitud_deg: float
    fecha_hora: datetime


@dataclass
class SolarPosition:
    """
    Resultado de la posición solar
    """

    azimuth_deg: float
    elevation_deg: float
    zenith_deg: float

    declination_deg: float
    hour_angle_deg: float


# ==========================================================
# MOTOR DE POSICIÓN SOLAR
# ==========================================================

def calcular_posicion_solar(entrada: SolarInput) -> SolarPosition:
    """
    Calcula la posición solar usando un modelo astronómico simplificado.
    """

    lat = entrada.latitud_deg
    fecha_hora = entrada.fecha_hora

    # día del año
    dia = fecha_hora.timetuple().tm_yday

    # hora decimal
    hora = fecha_hora.hour + fecha_hora.minute / 60

    # ------------------------------------------------------
    # Declinación solar
    # ------------------------------------------------------

    decl = 23.45 * sin(radians(360 * (284 + dia) / 365))

    # ------------------------------------------------------
    # Ángulo horario
    # ------------------------------------------------------

    hour_angle = 15 * (hora - 12)

    lat_r = radians(lat)
    decl_r = radians(decl)
    h_r = radians(hour_angle)

    # ------------------------------------------------------
    # Elevación solar
    # ------------------------------------------------------

    elevation = asin(
        sin(lat_r) * sin(decl_r)
        + cos(lat_r) * cos(decl_r) * cos(h_r)
    )

    elevation_deg = degrees(elevation)

    # ------------------------------------------------------
    # Ángulo cenital
    # ------------------------------------------------------

    zenith_deg = 90 - elevation_deg

    # ------------------------------------------------------
    # Azimut solar
    # ------------------------------------------------------

    az = acos(
        (
            sin(decl_r)
            - sin(elevation) * sin(lat_r)
        )
        /
        (cos(elevation) * cos(lat_r))
    )

    azimuth_deg = degrees(az)

    # ------------------------------------------------------
    # Resultado
    # ------------------------------------------------------

    return SolarPosition(
        azimuth_deg=azimuth_deg,
        elevation_deg=elevation_deg,
        zenith_deg=zenith_deg,
        declination_deg=decl,
        hour_angle_deg=hour_angle
    )
