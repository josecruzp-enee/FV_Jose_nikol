from __future__ import annotations

"""
SIMULACIÓN SOLAR 8760 — FV Engine

Responsabilidad
---------------
Transformar datos climáticos horarios en condiciones
solares del plano del generador FV.

Este módulo NO calcula:

• potencia FV
• energía generada
• pérdidas
• inversor

Solo produce el estado solar horario del sistema.

Pipeline
--------

ResultadoClima
      ↓
posición solar
      ↓
irradiancia en plano (POA)
      ↓
temperatura de celda
      ↓
EstadoSolarHora[8760]
"""

from dataclasses import dataclass
from typing import List

from solar.posicion_solar import calcular_posicion_solar
from solar.irradiancia_plano import calcular_irradiancia_plano
from electrical.paneles.modelo_termico import calcular_temperatura_celda

from .resultado_clima import ResultadoClima, validar_clima_8760


# ==========================================================
# ESTADO SOLAR POR HORA
# ==========================================================

@dataclass(frozen=True)
class EstadoSolarHora:
    """
    Condición solar del sistema en una hora específica.
    """

    poa_wm2: float
    temp_amb_c: float
    temp_celda_c: float

    zenith: float
    azimuth: float


# ==========================================================
# RESULTADO DEL MODELO 8760
# ==========================================================

@dataclass(frozen=True)
class ResultadoSolar8760:

    horas: List[EstadoSolarHora]

    poa_total_kwh_m2: float


# ==========================================================
# MOTOR DE SIMULACIÓN
# ==========================================================

def simular_clima_8760(
    clima: ResultadoClima,
    tilt: float,
    azimuth: float
) -> ResultadoSolar8760:

    validar_clima_8760(clima)

    horas: List[EstadoSolarHora] = []

    poa_total = 0.0


    # recorrer las 8760 horas
    for h in clima.horas:

        # posición solar
        pos = calcular_posicion_solar(
            timestamp=h.timestamp,
            lat=clima.latitud,
            lon=clima.longitud
        )

        # irradiancia en plano del generador
        poa = calcular_irradiancia_plano(
            ghi=h.ghi_wm2,
            zenith=pos.zenith,
            azimuth_solar=pos.azimuth,
            tilt=tilt,
            azimuth_superficie=azimuth
        )

        poa = max(0.0, poa)

        # temperatura de celda
        temp_celda = calcular_temperatura_celda(
            irradiancia_wm2=poa,
            temperatura_amb_c=h.temp_amb_c
        )

        poa_total += poa / 1000

        horas.append(
            EstadoSolarHora(
                poa_wm2=poa,
                temp_amb_c=h.temp_amb_c,
                temp_celda_c=temp_celda,
                zenith=pos.zenith,
                azimuth=pos.azimuth
            )
        )


    return ResultadoSolar8760(

        horas=horas,

        poa_total_kwh_m2=poa_total

    )
