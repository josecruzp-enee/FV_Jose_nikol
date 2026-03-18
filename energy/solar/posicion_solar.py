from __future__ import annotations

"""
MODELO DE POSICIÓN SOLAR — FV Engine
====================================

Responsabilidad
---------------

Calcular la posición del sol para una ubicación y fecha dada.

Parámetros calculados:

    • elevación
    • cenit
    • azimut
    • declinación
    • ángulo horario

Modelo implementado
-------------------

    ✔ aproximación astronómica estándar
    ✔ incluye ecuación del tiempo (mejora clave)

Frontera del dominio
--------------------

Entrada:
    SolarInput

Salida:
    SolarPosition

Consumido por:
    irradiancia_plano.py

Este módulo NO calcula energía.
"""

from dataclasses import dataclass
from datetime import datetime
from math import sin, cos, asin, acos, radians, degrees


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass(frozen=True)
class SolarInput:
    latitud_deg: float
    longitud_deg: float
    fecha_hora: datetime


@dataclass(frozen=True)
class SolarPosition:
    azimuth_deg: float
    elevation_deg: float
    zenith_deg: float
    declination_deg: float
    hour_angle_deg: float


# ==========================================================
# MOTOR DE POSICIÓN SOLAR
# ==========================================================

def calcular_posicion_solar(inp: SolarInput) -> SolarPosition:
    """
    Calcula la posición solar para una fecha y ubicación.

    Incluye:
        • corrección por ecuación del tiempo
        • corrección por longitud

    Nota:
        Modelo simplificado pero físicamente consistente.
    """

    lat = inp.latitud_deg
    lon = inp.longitud_deg
    fecha = inp.fecha_hora

    # ------------------------------------------------------
    # DÍA DEL AÑO
    # ------------------------------------------------------

    dia = fecha.timetuple().tm_yday

    # ------------------------------------------------------
    # HORA DECIMAL
    # ------------------------------------------------------

    hora = fecha.hour + fecha.minute / 60 + fecha.second / 3600

    # ------------------------------------------------------
    # ECUACIÓN DEL TIEMPO (min)
    # ------------------------------------------------------

    B = radians((360 / 365) * (dia - 81))

    eot = 9.87 * sin(2 * B) - 7.53 * cos(B) - 1.5 * sin(B)

    # ------------------------------------------------------
    # HORA SOLAR
    # ------------------------------------------------------

    hora_solar = hora + (eot / 60) + (lon / 15)

    # ------------------------------------------------------
    # DECLINACIÓN
    # ------------------------------------------------------

    decl = 23.45 * sin(radians(360 * (284 + dia) / 365))

    # ------------------------------------------------------
    # ÁNGULO HORARIO
    # ------------------------------------------------------

    hour_angle = 15 * (hora_solar - 12)

    # ------------------------------------------------------
    # CONVERSIÓN A RADIANES
    # ------------------------------------------------------

    lat_r = radians(lat)
    decl_r = radians(decl)
    h_r = radians(hour_angle)

    # ------------------------------------------------------
    # ELEVACIÓN
    # ------------------------------------------------------

    sin_elev = (
        sin(lat_r) * sin(decl_r)
        + cos(lat_r) * cos(decl_r) * cos(h_r)
    )

    sin_elev = max(-1.0, min(1.0, sin_elev))

    elevation = asin(sin_elev)
    elevation_deg = degrees(elevation)

    # ------------------------------------------------------
    # ZENITH
    # ------------------------------------------------------

    zenith_deg = 90 - elevation_deg

    # ------------------------------------------------------
    # AZIMUT ROBUSTO
    # ------------------------------------------------------

    if elevation_deg <= 0:
        # Sol bajo el horizonte → valor irrelevante
        azimuth_deg = 0.0
    else:
        cos_az = (
            sin(decl_r) - sin(elevation) * sin(lat_r)
        ) / (cos(elevation) * cos(lat_r))

        cos_az = max(-1.0, min(1.0, cos_az))

        az = acos(cos_az)
        azimuth_deg = degrees(az)

        # Corrección cuadrante
        if hour_angle > 0:
            azimuth_deg = 360 - azimuth_deg

    # ------------------------------------------------------
    # RESULTADO
    # ------------------------------------------------------

    return SolarPosition(
        azimuth_deg=azimuth_deg,
        elevation_deg=elevation_deg,
        zenith_deg=zenith_deg,
        declination_deg=decl,
        hour_angle_deg=hour_angle
    )


# ==========================================================
# ESTRUCTURA DEL DOMINIO
# ==========================================================

"""
Este módulo produce:

SolarPosition


Estructura:

SolarPosition
    ├─ azimuth_deg
    ├─ elevation_deg
    ├─ zenith_deg
    ├─ declination_deg
    └─ hour_angle_deg


Flujo de integración:

ResultadoClima
        ↓
calcular_posicion_solar
        ↓
irradiancia_plano
        ↓
simulacion_8760
        ↓
energy


Fronteras:

✔ clima → datos
✔ solar → geometría
✔ energy → potencia

Este módulo NO cruza esas fronteras.
"""
