from __future__ import annotations

"""
SIMULADOR ENERGÉTICO 8760 — FV Engine

Responsabilidad
---------------
Simular la producción energética anual de un sistema FV
hora por hora (8760).

Flujo físico:

clima
↓
posición solar
↓
irradiancia en plano (POA)
↓
modelo térmico
↓
potencia panel
↓
potencia string
↓
potencia AC
↓
energía acumulada

Salida
------
Producción:

• horaria
• mensual
• anual
• PR
• yield específico
"""

from dataclasses import dataclass
from typing import List

from solar.posicion_solar import calcular_posicion_solar
from solar.irradiancia_plano import calcular_irradiancia_plano
from solar.modelo_termico import calcular_temperatura_celda

from electrical.paneles.potencia_panel import (
    calcular_potencia_panel,
    PotenciaPanelInput
)

from .clima_modelo import ClimaHora


# ==========================================================
# RESULTADO DEL MOTOR
# ==========================================================

@dataclass
class ResultadoSimulacion8760:

    energia_horaria_kwh: List[float]

    energia_mensual_kwh: List[float]

    energia_anual_kwh: float

    yield_especifico_kwh_kwp: float

    performance_ratio: float


# ==========================================================
# HORAS POR MES
# ==========================================================

HORAS_MES = [
    744, 672, 744, 720, 744, 720,
    744, 744, 720, 744, 720, 744
]


# ==========================================================
# SIMULADOR
# ==========================================================

def simular_8760(

    clima: List[ClimaHora],

    lat: float,
    lon: float,

    tilt: float,
    azimuth: float,

    panel,

    n_paneles: int,

    eficiencia_inversor: float = 0.96

) -> ResultadoSimulacion8760:

    energia_horaria: List[float] = []

    energia_mensual = [0.0] * 12

    energia_anual = 0.0

    poa_total_kwh_m2 = 0.0

    potencia_dc_stc_kw = (panel.pmax_w * n_paneles) / 1000


    # ------------------------------------------------------
    # CONTROL DE MESES
    # ------------------------------------------------------

    mes_actual = 0
    horas_mes = HORAS_MES[0]
    contador_mes = 0


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

        poa_total_kwh_m2 += poa / 1000


        # --------------------------------------------------
        # TEMPERATURA DE CELDA
        # --------------------------------------------------

        t_cell = calcular_temperatura_celda(

            irradiancia_wm2=poa,

            temperatura_amb_c=hora_clima.temp_amb_c

        )


        # --------------------------------------------------
        # POTENCIA REAL DEL PANEL
        # --------------------------------------------------

        panel_real = calcular_potencia_panel(

            PotenciaPanelInput(

                irradiancia_poa_wm2=poa,

                temperatura_celda_c=t_cell,

                pmax_stc_w=panel.pmax_w,

                vmp_stc_v=panel.vmp_v,

                voc_stc_v=panel.voc_v,

                coef_pmax_pct_per_c=panel.gamma_p,

                coef_voc_pct_per_c=panel.beta_voc,

                coef_vmp_pct_per_c=panel.beta_vmp

            )

        )


        # --------------------------------------------------
        # POTENCIA DC DEL ARRAY
        # --------------------------------------------------

        p_dc = panel_real.pmp_w * n_paneles

        p_dc = max(p_dc, 0)


        # --------------------------------------------------
        # CONVERSIÓN A AC
        # --------------------------------------------------

        p_ac = p_dc * eficiencia_inversor


        # --------------------------------------------------
        # ENERGÍA HORARIA
        # --------------------------------------------------

        energia_kwh = p_ac / 1000

        energia_horaria.append(energia_kwh)

        energia_anual += energia_kwh


        # --------------------------------------------------
        # ENERGÍA MENSUAL
        # --------------------------------------------------

        energia_mensual[mes_actual] += energia_kwh

        contador_mes += 1

        if contador_mes >= horas_mes:

            mes_actual += 1

            if mes_actual > 11:
                mes_actual = 11

            contador_mes = 0

            horas_mes = HORAS_MES[mes_actual]


    # ------------------------------------------------------
    # YIELD ESPECÍFICO
    # ------------------------------------------------------

    yield_especifico = energia_anual / potencia_dc_stc_kw


    # ------------------------------------------------------
    # PERFORMANCE RATIO
    # ------------------------------------------------------

    if poa_total_kwh_m2 > 0:

        pr = energia_anual / (potencia_dc_stc_kw * poa_total_kwh_m2)

    else:

        pr = 0


    return ResultadoSimulacion8760(

        energia_horaria_kwh=energia_horaria,

        energia_mensual_kwh=energia_mensual,

        energia_anual_kwh=energia_anual,

        yield_especifico_kwh_kwp=yield_especifico,

        performance_ratio=pr

    )
