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

def calcular_posicion_solar(entrada: SolarInput) -> SolarPosition:

    lat = entrada.latitud_deg
    lon = entrada.longitud_deg
    fecha_hora = entrada.fecha_hora

    # día del año
    dia = fecha_hora.timetuple().tm_yday

    # hora decimal
    hora = fecha_hora.hour + fecha_hora.minute / 60

    # ------------------------------------------------------
    # CORRECCIÓN POR LONGITUD (aprox)
    # ------------------------------------------------------

    offset = lon / 15
    hora_solar = hora + offset

    # ------------------------------------------------------
    # DECLINACIÓN
    # ------------------------------------------------------

    decl = 23.45 * sin(radians(360 * (284 + dia) / 365))

    # ------------------------------------------------------
    # ÁNGULO HORARIO
    # ------------------------------------------------------

    hour_angle = 15 * (hora_solar - 12)

    lat_r = radians(lat)
    decl_r = radians(decl)
    h_r = radians(hour_angle)

    # ------------------------------------------------------
    # ELEVACIÓN
    # ------------------------------------------------------

    elevation = asin(
        sin(lat_r) * sin(decl_r)
        + cos(lat_r) * cos(decl_r) * cos(h_r)
    )

    elevation_deg = degrees(elevation)

    # ------------------------------------------------------
    # ZENITH
    # ------------------------------------------------------

    zenith_deg = 90 - elevation_deg

    # ------------------------------------------------------
    # AZIMUTH ROBUSTO
    # ------------------------------------------------------

    x = (
        sin(decl_r) - sin(elevation) * sin(lat_r)
    ) / (cos(elevation) * cos(lat_r))

    x = max(-1.0, min(1.0, x))

    az = acos(x)
    azimuth_deg = degrees(az)

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
