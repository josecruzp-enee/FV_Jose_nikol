from __future__ import annotations

"""
SIMULACIÓN ENERGÉTICA 8760 — FV Engine

Responsabilidad
---------------
Simular la producción energética del sistema FV
durante todas las horas del año.

Este módulo coordina:

clima
solar
paneles
inversor
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from solar.entrada_solar import EntradaSolar
from solar.orquestador_solar import ejecutar_solar

from electrical.energia.clima_tmy import generar_clima_base


# ==========================================================
# GENERADOR DE HORAS DEL AÑO
# ==========================================================

def generar_horas_anio(anio: int) -> List[datetime]:

    inicio = datetime(anio, 1, 1, 0, 0)

    return [
        inicio + timedelta(hours=i)
        for i in range(8760)
    ]


# ==========================================================
# SIMULACIÓN 8760
# ==========================================================

def simular_8760(
    lat: float,
    lon: float,
    tilt_deg: float,
    azimuth_panel_deg: float,
    anio: int = 2024
) -> Dict[str, Any]:

    horas = generar_horas_anio(anio)

    clima = generar_clima_base()

    energia_total = 0

    produccion_horaria = []

    for i, fecha in enumerate(horas):

        ghi = clima[i].ghi_wm2

        entrada_solar = EntradaSolar(
            lat=lat,
            lon=lon,
            fecha_hora=fecha,
            ghi_wm2=ghi,
            tilt_deg=tilt_deg,
            azimuth_panel_deg=azimuth_panel_deg
        )

        solar = ejecutar_solar(entrada_solar)

        if not solar["ok"]:
            produccion_horaria.append(0)
            continue

        poa = solar["poa_wm2"]

        # energía simplificada (temporal)
        energia_hora = poa * 0.001

        energia_total += energia_hora

        produccion_horaria.append(energia_hora)

    return {

        "energia_anual_kwh": energia_total,

        "produccion_horaria": produccion_horaria,

        "horas_simuladas": len(produccion_horaria)

    }
