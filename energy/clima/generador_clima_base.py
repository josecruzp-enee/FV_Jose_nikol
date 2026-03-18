from __future__ import annotations

from datetime import datetime, timedelta
from typing import List
from math import sin, pi

from .resultado_clima import ResultadoClima, ClimaHora


# ==========================================================
# GENERADOR DE CLIMA SINTÉTICO
# ==========================================================

def generar_clima_base() -> ResultadoClima:

    horas: List[ClimaHora] = []

    inicio = datetime(2020, 1, 1, 0, 0)

    for h in range(8760):

        timestamp = inicio + timedelta(hours=h)

        hora_dia = timestamp.hour
        dia_anio = timestamp.timetuple().tm_yday

        # --------------------------------------------------
        # IRRADIANCIA DIARIA
        # --------------------------------------------------

        if 6 <= hora_dia <= 18:
            angulo = (hora_dia - 6) / 12 * pi
            ghi = 900 * sin(angulo)
        else:
            ghi = 0.0

        # --------------------------------------------------
        # VARIACIÓN ESTACIONAL
        # --------------------------------------------------

        factor_estacional = 0.75 + 0.25 * sin(2 * pi * dia_anio / 365)

        ghi *= factor_estacional
        ghi = max(0.0, ghi)

        # --------------------------------------------------
        # COMPONENTES DIRECTA Y DIFUSA
        # --------------------------------------------------

        dni = ghi * 0.7
        dhi = ghi * 0.3

        # --------------------------------------------------
        # TEMPERATURA AMBIENTE
        # --------------------------------------------------

        temp_base = 28
        temp_variacion = 6 * sin(2 * pi * hora_dia / 24)

        temp = temp_base + temp_variacion

        # 🔥 FIX: agregar viento_ms

        horas.append(
            ClimaHora(
                timestamp=timestamp,
                ghi_wm2=ghi,
                dni_wm2=dni,
                dhi_wm2=dhi,
                temp_amb_c=temp,
                viento_ms=1.0  # ✔ requerido por contrato
            )
        )

    return ResultadoClima(
        horas=horas,
        latitud=0.0,
        longitud=0.0,
        fuente="sintetico",
        meta={"modelo": "clima_base"}
    )
