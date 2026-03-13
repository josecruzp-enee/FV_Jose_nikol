"""
IRRADIANCIA EN PLANO INCLINADO — FV Engine

Dominio: solar

Responsabilidad
---------------
Calcular la irradiancia que incide sobre el plano del panel FV.

Implementa un modelo isotrópico simple ampliamente utilizado
para simulaciones energéticas preliminares.

POA = Directa + Difusa + Reflejada
"""

from dataclasses import dataclass
from math import cos, sin, radians


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass
class IrradianciaInput:

    dni: float
    dhi: float
    ghi: float

    solar_zenith_deg: float
    solar_azimuth_deg: float

    panel_tilt_deg: float
    panel_azimuth_deg: float

    albedo: float = 0.2


@dataclass
class IrradianciaPlano:

    poa_total: float
    poa_directa: float
    poa_difusa: float
    poa_reflejada: float


# ==========================================================
# CÁLCULO DEL ÁNGULO DE INCIDENCIA
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

    return max(cos_theta, 0)


# ==========================================================
# MOTOR DE IRRADIANCIA
# ==========================================================

def calcular_irradiancia_plano(inp: IrradianciaInput) -> IrradianciaPlano:

    cos_theta = _cos_theta_i(inp)

    tilt = radians(inp.panel_tilt_deg)

    # componente directa
    poa_directa = inp.dni * cos_theta

    # componente difusa
    poa_difusa = inp.dhi * (1 + cos(tilt)) / 2

    # componente reflejada
    poa_reflejada = inp.ghi * inp.albedo * (1 - cos(tilt)) / 2

    poa_total = poa_directa + poa_difusa + poa_reflejada

    return IrradianciaPlano(
        poa_total=poa_total,
        poa_directa=poa_directa,
        poa_difusa=poa_difusa,
        poa_reflejada=poa_reflejada
    )
