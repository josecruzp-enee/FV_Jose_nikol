from __future__ import annotations

from dataclasses import dataclass
from typing import List

# ----------------------------------------------------------
# DEPENDENCIAS
# ----------------------------------------------------------

from energy.solar.posicion_solar import (
    calcular_posicion_solar,
    SolarInput,
)

from energy.solar.irradiancia_plano import (
    calcular_irradiancia_plano,
    IrradianciaInput
)

from .resultado_clima import ResultadoClima, validar_clima_8760


# ==========================================================
# ESTADO SOLAR HORARIO
# ==========================================================

@dataclass(frozen=True)
class EstadoSolarHora:

    poa_wm2: float
    temp_amb_c: float

    zenith: float
    azimuth: float


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class ResultadoClima8760:

    horas: List[EstadoSolarHora]
    poa_total_kwh_m2: float


# ==========================================================
# ORQUESTADOR
# ==========================================================

def simular_clima_8760(
    clima: ResultadoClima,
    tilt: float,
    azimuth: float
) -> ResultadoClima8760:

    validar_clima_8760(clima)

    horas: List[EstadoSolarHora] = []
    poa_total_kwh_m2 = 0.0

    for hora in clima.horas:

        # --------------------------------------------------
        # 1. POSICIÓN SOLAR
        # --------------------------------------------------

        pos = calcular_posicion_solar(
            SolarInput(
                latitud_deg=clima.latitud,
                longitud_deg=clima.longitud,
                fecha_hora=hora.timestamp
            )
        )

        # --------------------------------------------------
        # 2. POA
        # --------------------------------------------------

        irr = calcular_irradiancia_plano(
            IrradianciaInput(
                dni=hora.dni_wm2,
                dhi=hora.dhi_wm2,
                ghi=hora.ghi_wm2,
                solar_zenith_deg=pos.zenith_deg,
                solar_azimuth_deg=pos.azimuth_deg,
                panel_tilt_deg=tilt,
                panel_azimuth_deg=azimuth
            )
        )

        poa = max(0.0, irr.poa_total)

        # --------------------------------------------------
        # 3. ACUMULACIÓN ENERGÍA
        # --------------------------------------------------

        poa_total_kwh_m2 += poa / 1000.0

        # --------------------------------------------------
        # 4. ESTADO
        # --------------------------------------------------

        horas.append(
            EstadoSolarHora(
                poa_wm2=poa,
                temp_amb_c=hora.temp_amb_c,
                zenith=pos.zenith_deg,
                azimuth=pos.azimuth_deg
            )
        )

    return ResultadoClima8760(
        horas=horas,
        poa_total_kwh_m2=poa_total_kwh_m2
    )
