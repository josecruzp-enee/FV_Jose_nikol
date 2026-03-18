from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .entrada_solar import EntradaSolar
from .posicion_solar import (
    calcular_posicion_solar,
    SolarInput
)
from .irradiancia_plano import (
    calcular_irradiancia_plano,
    IrradianciaInput
)


# ==========================================================
# SALIDA
# ==========================================================

@dataclass(frozen=True)
class SolarResultado:
    poa_wm2: float
    zenith_deg: float
    azimuth_deg: float


# ==========================================================
# VALIDACIÓN
# ==========================================================

def _validar(e: EntradaSolar):

    if e.lat is None or e.lon is None:
        raise ValueError("Lat/lon inválidos")

    if e.fecha_hora is None:
        raise ValueError("fecha_hora requerida")

    if e.dni_wm2 < 0 or e.dhi_wm2 < 0 or e.ghi_wm2 < 0:
        raise ValueError("Irradiancia negativa")

    if e.tilt_deg is None or e.azimuth_panel_deg is None:
        raise ValueError("Geometría inválida")


# ==========================================================
# ORQUESTADOR
# ==========================================================

def ejecutar_solar(entrada: EntradaSolar) -> SolarResultado:

    _validar(entrada)

    # ------------------------------------------------------
    # POSICIÓN SOLAR
    # ------------------------------------------------------

    pos = calcular_posicion_solar(
        SolarInput(
            latitud_deg=entrada.lat,
            longitud_deg=entrada.lon,
            fecha_hora=entrada.fecha_hora
        )
    )

    # ------------------------------------------------------
    # IRRADIANCIA EN PLANO
    # ------------------------------------------------------

    irr = calcular_irradiancia_plano(
        IrradianciaInput(
            dni=entrada.dni_wm2,
            dhi=entrada.dhi_wm2,
            ghi=entrada.ghi_wm2,
            solar_zenith_deg=pos.zenith_deg,
            solar_azimuth_deg=pos.azimuth_deg,
            panel_tilt_deg=entrada.tilt_deg,
            panel_azimuth_deg=entrada.azimuth_panel_deg
        )
    )

    # ------------------------------------------------------
    # RESULTADO
    # ------------------------------------------------------

    return SolarResultado(
        poa_wm2=irr.poa_total,
        zenith_deg=pos.zenith_deg,
        azimuth_deg=pos.azimuth_deg
    )
