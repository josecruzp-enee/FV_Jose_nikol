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
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from solar.entrada_solar import EntradaSolar
from solar.orquestador_solar import ejecutar_solar

from electrical.energia.clima_tmy import generar_clima_base
from electrical.paneles.potencia_panel import evaluar_panel_en_operacion

from electrical.modelos.paneles import PanelSpec


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
    panel: PanelSpec,
    n_paneles_total: int,
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
        temp_amb = clima[i].temp_amb_c

        # ------------------------------------------------------
        # SOLAR
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # PANEL
        # ------------------------------------------------------

        panel_real = evaluar_panel_en_operacion(
            panel=panel,
            temperatura_amb_c=temp_amb,
            irradiancia_wm2=poa
        )

        potencia_panel = panel_real["pmp_w"]

        # ------------------------------------------------------
        # ARRAY FV
        # ------------------------------------------------------

        potencia_array = potencia_panel * n_paneles_total

        # ------------------------------------------------------
        # ENERGÍA DE LA HORA
        # ------------------------------------------------------

        energia_hora = potencia_array / 1000  # kWh

        energia_total += energia_hora

        produccion_horaria.append(energia_hora)

    # ==========================================================
    # RESULTADO FINAL
    # ==========================================================

    return {

        "energia_anual_kwh": energia_total,

        "produccion_horaria": produccion_horaria,

        "horas_simuladas": len(produccion_horaria)

    }
