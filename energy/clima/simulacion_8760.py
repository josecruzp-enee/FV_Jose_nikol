from __future__ import annotations

"""
SIMULADOR CLIMÁTICO 8760 — FV Engine

Genera las condiciones solares horarias del año.

NO calcula:
- potencia FV
- energía generada
- pérdidas
- inversor
"""

from dataclasses import dataclass
from typing import List

from energy.solar.posicion_solar import (
    calcular_posicion_solar,
    SolarInput,
)

from energy.solar.irradiancia_plano import calcular_irradiancia_plano
from energy.panel_energia.modelo_termico import calcular_temperatura_celda

from .resultado_clima import ResultadoClima, validar_clima_8760


# ==========================================================
# ESTADO SOLAR HORARIO
# ==========================================================

@dataclass(frozen=True)
class EstadoSolarHora:

    poa_wm2: float
    temp_amb_c: float
    temp_celda_c: float
    zenith: float
    azimuth: float


# ==========================================================
# RESULTADO CLIMA 8760
# ==========================================================

@dataclass(frozen=True)
class ResultadoClima8760:

    horas: List[EstadoSolarHora]
    poa_total_kwh_m2: float


# ==========================================================
# SIMULACIÓN
# ==========================================================
def simular_clima_8760(
    clima: ResultadoClima,
    tilt: float,
    azimuth: float
) -> ResultadoClima8760:

    from energy.solar.posicion_solar import SolarInput
    from energy.solar.irradiancia_plano import IrradianciaInput

    # validar que existan 8760 registros
    validar_clima_8760(clima)

    horas: List[EstadoSolarHora] = []
    poa_total_kwh_m2 = 0.0

    # recorrer las 8760 horas del año
    for hora in clima.horas:

        # ======================================================
        # 1. POSICIÓN SOLAR
        # ======================================================

        pos = calcular_posicion_solar(
            SolarInput(
                latitud_deg=clima.latitud,
                longitud_deg=clima.longitud,
                fecha_hora=hora.timestamp
            )
        )

        # ======================================================
        # 2. IRRADIANCIA EN PLANO (POA)
        # ======================================================

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

        # ======================================================
        # 3. TEMPERATURA DE CELDA
        # ======================================================

        from energy.panel_energia.modelo_termico import ModeloTermicoInput

        r_termico = calcular_temperatura_celda(
            ModeloTermicoInput(
                irradiancia_poa_wm2=poa,
                temperatura_ambiente_c=hora.temp_amb_c,
                noct_c=45  # ⚠️ puedes parametrizar después
            )
        )

        temp_celda = r_termico.temperatura_celda_c

        # ======================================================
        # 4. ACUMULACIÓN ENERGÍA
        # ======================================================

        poa_total_kwh_m2 += poa / 1000  # Wh → kWh

        # ======================================================
        # 5. ESTADO HORARIO
        # ======================================================

        horas.append(
            EstadoSolarHora(
                poa_wm2=poa,
                temp_amb_c=hora.temp_amb_c,
                temp_celda_c=temp_celda,
                zenith=pos.zenith_deg,
                azimuth=pos.azimuth_deg
            )
        )

    # ======================================================
    # RESULTADO FINAL
    # ======================================================

    return ResultadoClima8760(
        horas=horas,
        poa_total_kwh_m2=poa_total_kwh_m2
    )
