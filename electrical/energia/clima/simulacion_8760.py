from __future__ import annotations

"""
SIMULADOR CLIMÁTICO 8760 — FV Engine

Dominio
-------
electrical.energia.clima

Responsabilidad
---------------
Generar las condiciones solares horarias necesarias
para la simulación energética del sistema FV.

Este módulo NO calcula:

• potencia del panel
• potencia del sistema
• energía generada
• clipping del inversor

Solo calcula variables físicas del entorno.

Flujo físico modelado
---------------------

clima (GHI + temperatura)
↓
posición solar
↓
irradiancia en plano del generador (POA)
↓
temperatura de celda

Salida
------

Serie horaria (8760) con:

• POA
• temperatura ambiente
• temperatura celda
• posición solar
"""

from dataclasses import dataclass
from typing import List

from solar.posicion_solar import calcular_posicion_solar
from solar.irradiancia_plano import calcular_irradiancia_plano
from electrical.paneles.modelo_termico import calcular_temperatura_celda

from .resultado_clima import ClimaHora


# ==========================================================
# MODELO DE SALIDA
# ==========================================================

@dataclass
class EstadoSolarHora:
    """
    Estado solar del sistema para una hora específica.
    """

    poa_wm2: float

    temp_amb_c: float

    temp_celda_c: float

    zenith: float

    azimuth: float


# ==========================================================
# RESULTADO DE SIMULACIÓN
# ==========================================================

@dataclass
class ResultadoClima8760:
    """
    Serie completa de condiciones solares del año.
    """

    horas: List[EstadoSolarHora]

    poa_total_kwh_m2: float


# ==========================================================
# SIMULADOR CLIMÁTICO
# ==========================================================

def simular_clima_8760(

    clima: List[ClimaHora],

    lat: float,
    lon: float,

    tilt: float,
    azimuth: float

) -> ResultadoClima8760:
    """
    Genera la serie horaria de condiciones solares
    para el plano del generador FV.
    """

    if len(clima) != 8760:
        raise ValueError("La serie climática debe tener 8760 horas.")

    horas: List[EstadoSolarHora] = []

    poa_total_kwh_m2 = 0.0


    # ======================================================
    # SIMULACIÓN HORARIA
    # ======================================================

    for h, hora_clima in enumerate(clima):

        # --------------------------------------------------
        # POSICIÓN SOLAR
        # --------------------------------------------------

        pos = calcular_posicion_solar(

            hora_anual=h,

            lat=lat,

            lon=lon

        )


        # --------------------------------------------------
        # IRRADIANCIA EN PLANO DEL GENERADOR
        # --------------------------------------------------

        poa = calcular_irradiancia_plano(

            ghi=hora_clima.ghi_wm2,

            zenith=pos.zenith,

            azimuth_solar=pos.azimuth,

            tilt=tilt,

            azimuth_superficie=azimuth

        )


        # --------------------------------------------------
        # TEMPERATURA DE CELDA
        # --------------------------------------------------

        t_cell = calcular_temperatura_celda(

            irradiancia_wm2=poa,

            temperatura_amb_c=hora_clima.temp_amb_c

        )


        # --------------------------------------------------
        # ACUMULAR POA
        # --------------------------------------------------

        if poa > 0:
            poa_total_kwh_m2 += poa / 1000


        horas.append(

            EstadoSolarHora(

                poa_wm2=poa,

                temp_amb_c=hora_clima.temp_amb_c,

                temp_celda_c=t_cell,

                zenith=pos.zenith,

                azimuth=pos.azimuth

            )

        )


    return ResultadoClima8760(

        horas=horas,

        poa_total_kwh_m2=poa_total_kwh_m2

    )
