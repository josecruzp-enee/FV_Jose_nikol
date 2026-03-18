from dataclasses import dataclass
from math import cos, sin, radians


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass(frozen=True)
class IrradianciaInput:
    dni: float
    dhi: float
    ghi: float
    solar_zenith_deg: float
    solar_azimuth_deg: float
    panel_tilt_deg: float
    panel_azimuth_deg: float
    albedo: float = 0.2


@dataclass(frozen=True)
class IrradianciaPlano:
    poa_total: float
    poa_directa: float
    poa_difusa: float
    poa_reflejada: float


# ==========================================================
# ÁNGULO DE INCIDENCIA
# ==========================================================

def _cos_theta_i(inp: IrradianciaInput):

    zen = radians(inp.solar_zenith_deg)
    az = radians(inp.solar_azimuth_deg)

    tilt = radians(inp.panel_tilt_deg)
    panel_az = radians(inp.panel_azimuth_deg)

    cos_theta = (
        cos(zen) * cos(tilt)
        +
        sin(zen) * sin(tilt) * cos(az - panel_az)
    )

    return max(cos_theta, 0.0)


# ==========================================================
# MOTOR DE IRRADIANCIA
# ==========================================================

def calcular_irradiancia_plano(inp: IrradianciaInput) -> IrradianciaPlano:

    # validación básica
    if inp.dni < 0 or inp.dhi < 0 or inp.ghi < 0:
        raise ValueError("Irradiancia negativa no válida")

    cos_theta = _cos_theta_i(inp)

    tilt = radians(inp.panel_tilt_deg)

    # ------------------------------------------------------
    # DIRECTA
    # ------------------------------------------------------

    if inp.solar_zenith_deg >= 90:
        poa_directa = 0.0
    else:
        poa_directa = inp.dni * cos_theta

    # ------------------------------------------------------
    # DIFUSA (isotrópico)
    # ------------------------------------------------------

    poa_difusa = inp.dhi * (1 + cos(tilt)) / 2

    # ------------------------------------------------------
    # REFLEJADA
    # ------------------------------------------------------

    poa_reflejada = inp.ghi * inp.albedo * (1 - cos(tilt)) / 2

    # ------------------------------------------------------
    # TOTAL
    # ------------------------------------------------------

    poa_total = max(
        poa_directa + poa_difusa + poa_reflejada,
        0.0
    )

    return IrradianciaPlano(
        poa_total=poa_total,
        poa_directa=poa_directa,
        poa_difusa=poa_difusa,
        poa_reflejada=poa_reflejada
    )
