"""
POSICIÓN SOLAR — FV Engine

Dominio: solar

Responsabilidad
----------------
Calcular la posición del sol para una fecha y ubicación geográfica.

Este módulo implementa un modelo astronómico simplificado
adecuado para simulación energética de sistemas FV.
"""

from dataclasses import dataclass
from datetime import datetime
from math import sin, cos, asin, acos, radians, degrees


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass
class SolarInput:

    latitud_deg: float
    longitud_deg: float
    fecha_hora: datetime


@dataclass
class SolarPosition:

    azimuth_deg: float
    elevation_deg: float
    zenith_deg: float

    declination_deg: float
    hour_angle_deg: float


# ==========================================================
# MOTOR DE POSICIÓN SOLAR
# ==========================================================

def calcular_posicion_solar(entrada: SolarInput) -> SolarPosition:

    lat = entrada.latitud_deg
    fecha_hora = entrada.fecha_hora

    dia = fecha_hora.timetuple().tm_yday
    hora = fecha_hora.hour + fecha_hora.minute / 60

    # declinación solar
    decl = 23.45 * sin(radians(360 * (284 + dia) / 365))

    # ángulo horario
    h = 15 * (hora - 12)

    lat_r = radians(lat)
    decl_r = radians(decl)
    h_r = radians(h)

    # elevación solar
    elev = asin(
        sin(lat_r) * sin(decl_r)
        + cos(lat_r) * cos(decl_r) * cos(h_r)
    )

    elev_deg = degrees(elev)

    # zenith
    zenith = 90 - elev_deg

    # azimut
    az = acos(
        (
            sin(decl_r)
            - sin(elev) * sin(lat_r)
        )
        /
        (cos(elev) * cos(lat_r))
    )

    azimuth = degrees(az)

    return SolarPosition(
        azimuth_deg=azimuth,
        elevation_deg=elev_deg,
        zenith_deg=zenith,
        declination_deg=decl,
        hour_angle_deg=h
    )
