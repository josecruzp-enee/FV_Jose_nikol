"""
POSICIÓN SOLAR — FV Engine

Este módulo calcula la posición del sol para una fecha y hora
específica usando un modelo astronómico simplificado.

Entradas
--------
lat : float
    Latitud en grados

lon : float
    Longitud en grados

fecha_hora : datetime

Salidas
-------
dict:

{
    "azimuth_deg": float,
    "elevation_deg": float,
    "zenith_deg": float
}
"""

from math import sin, cos, tan, asin, acos, radians, degrees
from datetime import datetime


def posicion_solar(lat: float, lon: float, fecha_hora: datetime):

    dia = fecha_hora.timetuple().tm_yday
    hora = fecha_hora.hour + fecha_hora.minute / 60

    # declinación solar
    decl = 23.45 * sin(radians(360 * (284 + dia) / 365))

    # ángulo horario
    h = 15 * (hora - 12)

    lat_r = radians(lat)
    decl_r = radians(decl)
    h_r = radians(h)

    elev = asin(
        sin(lat_r) * sin(decl_r)
        + cos(lat_r) * cos(decl_r) * cos(h_r)
    )

    zenith = 90 - degrees(elev)

    az = acos(
        (
            sin(decl_r)
            - sin(elev) * sin(lat_r)
        )
        /
        (cos(elev) * cos(lat_r))
    )

    azimuth = degrees(az)

    return {
        "azimuth_deg": azimuth,
        "elevation_deg": degrees(elev),
        "zenith_deg": zenith
    }
