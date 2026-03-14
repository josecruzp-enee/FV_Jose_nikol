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

from .resultado_clima import ResultadoClima, validar_clima_8760


# ==========================================================
# ESTADO SOLAR POR HORA
# ==========================================================

@dataclass(frozen=True)
class EstadoSolarHora:
    """
    Estado físico del sistema solar en una hora específica.

    Contiene las variables necesarias para calcular luego
    la potencia del generador fotovoltaico.
    """

    # Irradiancia en el plano del generador (Plane Of Array)
    poa_wm2: float

    # Temperatura ambiente
    temp_amb_c: float

    # Temperatura de celda del módulo FV
    temp_celda_c: float

    # Ángulo cenital solar
    zenith: float

    # Azimut solar
    azimuth: float


# ==========================================================
# RESULTADO DE SIMULACIÓN CLIMÁTICA
# ==========================================================

@dataclass(frozen=True)
class ResultadoClima8760:
    """
    Serie completa de condiciones solares para el año.

    Este objeto será consumido posteriormente por
    el motor energético del sistema FV.
    """

    # Serie horaria completa
    horas: List[EstadoSolarHora]

    # Irradiancia total anual en el plano del generador
    poa_total_kwh_m2: float


# ==========================================================
# SIMULADOR CLIMÁTICO
# ==========================================================

def simular_clima_8760(
    clima: ResultadoClima,
    tilt: float,
    azimuth: float
) -> ResultadoClima8760:
    """
    Genera la serie horaria de condiciones solares
    para el plano del generador fotovoltaico.

    Parámetros
    ----------
    clima : ResultadoClima
        Serie climática base (GHI + temperatura).

    tilt : float
        Inclinación del generador FV (grados).

    azimuth : float
        Azimut del generador FV (grados).

    Retorna
    -------
    ResultadoClima8760
        Serie horaria con POA, temperatura de celda
        y posición solar.
    """

    # ------------------------------------------------------
    # VALIDAR SERIE CLIMÁTICA
    # ------------------------------------------------------

    # Se asegura que la serie tenga exactamente 8760 horas
    validar_clima_8760(clima)

    # Lista donde se almacenará el estado solar horario
    horas: List[EstadoSolarHora] = []

    # Irradiancia anual acumulada
    poa_total_kwh_m2 = 0.0


    # ======================================================
    # SIMULACIÓN HORARIA
    # ======================================================

    for hora_clima in clima.horas:

        # --------------------------------------------------
        # POSICIÓN SOLAR
        # --------------------------------------------------

        # Se calcula la posición solar en función del tiempo
        # y la ubicación geográfica del sistema.

        pos = calcular_posicion_solar(
            timestamp=hora_clima.timestamp,
            lat=clima.latitud,
            lon=clima.longitud
        )


        # --------------------------------------------------
        # IRRADIANCIA EN PLANO DEL GENERADOR (POA)
        # --------------------------------------------------

        # Se transforma la irradiancia horizontal (GHI)
        # al plano del generador FV considerando:

        # • inclinación del generador
        # • orientación del generador
        # • posición solar

        poa = calcular_irradiancia_plano(
            ghi=hora_clima.ghi_wm2,
            zenith=pos.zenith,
            azimuth_solar=pos.azimuth,
            tilt=tilt,
            azimuth_superficie=azimuth
        )

        # Seguridad física: evitar valores negativos
        poa = max(0.0, poa)


        # --------------------------------------------------
        # TEMPERATURA DE CELDA
        # --------------------------------------------------

        # Se calcula la temperatura de operación del módulo
        # en función de:

        # • irradiancia incidente
        # • temperatura ambiente

        temp_celda = calcular_temperatura_celda(
            irradiancia_wm2=poa,
            temperatura_amb_c=hora_clima.temp_amb_c
        )


        # --------------------------------------------------
        # ACUMULAR IRRADIANCIA ANUAL
        # --------------------------------------------------

        # Conversión:
        # W/m² durante 1 hora → Wh/m²

        if poa > 0:

            poa_total_kwh_m2 += poa / 1000


        # --------------------------------------------------
        # GUARDAR ESTADO SOLAR HORARIO
        # --------------------------------------------------

        horas.append(
            EstadoSolarHora(
                poa_wm2=poa,
                temp_amb_c=hora_clima.temp_amb_c,
                temp_celda_c=temp_celda,
                zenith=pos.zenith,
                azimuth=pos.azimuth
            )
        )


    # ======================================================
    # RESULTADO FINAL
    # ======================================================

    return ResultadoClima8760(
        horas=horas,
        poa_total_kwh_m2=poa_total_kwh_m2
    )
