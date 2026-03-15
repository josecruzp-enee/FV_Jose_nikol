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

from solar.posicion_solar import calcular_posicion_solar
from solar.irradiancia_plano import calcular_irradiancia_plano
from electrical.paneles.modelo_termico import calcular_temperatura_celda

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

    # validar que existan 8760 registros
    validar_clima_8760(clima)

    horas: List[EstadoSolarHora] = []

    poa_total_kwh_m2 = 0.0

    # recorrer las 8760 horas del año
    for hora in clima.horas:

        # posición solar
        pos = calcular_posicion_solar(
            timestamp=hora.timestamp,
            lat=clima.latitud,
            lon=clima.longitud
        )

        # irradiancia en plano del generador
        poa = calcular_irradiancia_plano(
            ghi=hora.ghi_wm2,
            zenith=pos.zenith,
            azimuth_solar=pos.azimuth,
            tilt=tilt,
            azimuth_superficie=azimuth
        )

        poa = max(0.0, poa)

        # temperatura de celda
        temp_celda = calcular_temperatura_celda(
            irradiancia_wm2=poa,
            temperatura_amb_c=hora.temp_amb_c
        )

        # acumular irradiancia anual
        poa_total_kwh_m2 += poa / 1000

        horas.append(
            EstadoSolarHora(
                poa_wm2=poa,
                temp_amb_c=hora.temp_amb_c,
                temp_celda_c=temp_celda,
                zenith=pos.zenith,
                azimuth=pos.azimuth
            )
        )

    return ResultadoClima8760(
        horas=horas,
        poa_total_kwh_m2=poa_total_kwh_m2
    )
