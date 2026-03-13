from __future__ import annotations

"""
GENERADOR DE CLIMA BASE — FV Engine

Responsabilidad
---------------
Generar un clima sintético de 8760 horas para
simulaciones cuando no se dispone de datos
reales (PVGIS / TMY).

Datos generados:
    • GHI (irradiancia horizontal)
    • temperatura ambiente

Este modelo es simplificado y sirve como
placeholder para pruebas del motor energético.
"""

from typing import List
from math import sin, pi

from .clima_modelo import ClimaHora


# ==========================================================
# GENERADOR DE CLIMA SINTÉTICO
# ==========================================================

def generar_clima_base() -> List[ClimaHora]:

    clima: List[ClimaHora] = []

    for h in range(8760):

        hora_dia = h % 24
        dia_anio = h // 24

        # --------------------------------------------------
        # IRRADIANCIA DIARIA (forma sinusoidal)
        # --------------------------------------------------

        if 6 <= hora_dia <= 18:

            angulo = (hora_dia - 6) / 12 * pi
            ghi = 900 * sin(angulo)

        else:

            ghi = 0

        # --------------------------------------------------
        # VARIACIÓN ESTACIONAL
        # --------------------------------------------------

        factor_estacional = 0.75 + 0.25 * sin(2 * pi * dia_anio / 365)

        ghi *= factor_estacional

        # --------------------------------------------------
        # TEMPERATURA AMBIENTE
        # --------------------------------------------------

        temp_base = 28
        temp_variacion = 6 * sin(2 * pi * hora_dia / 24)

        temp = temp_base + temp_variacion

        clima.append(

            ClimaHora(
                ghi_wm2=max(0, ghi),
                temp_amb_c=temp
            )

        )

    return clima
