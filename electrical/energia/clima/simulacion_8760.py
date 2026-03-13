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
potencia DC array
↓
potencia AC inversor
↓
energía horaria

Salida
------
Producción horaria + métricas del sistema.
"""

from dataclasses import dataclass
from typing import List

from solar.posicion_solar import calcular_posicion_solar
from solar.irradiancia_plano import calcular_irradiancia_plano
from electrical.paneles.modelo_termico import calcular_temperatura_celda

from electrical.paneles.potencia_panel import (
    calcular_potencia_panel,
    PotenciaPanelInput
)

from .resultado_clima import ClimaHora


# ==========================================================
# RESULTADO DEL MOTOR
# ==========================================================

@dataclass
class ResultadoSimulacion8760:

    energia_horaria_kwh: List[float]

    energia_anual_kwh: float

    yield_especifico_kwh_kwp: float

    performance_ratio: float

    poa_total_kwh_m2: float


# ==========================================================
# SIMULADOR 8760
# ==========================================================

def simular_8760(

    clima: List[ClimaHora],

    lat: float,
    lon: float,

    tilt: float,
    azimuth: float,

    panel,

    n_paneles: int,

    pac_nominal_kw: float,

    eficiencia_inversor: float = 0.96

) -> ResultadoSimulacion8760:

    if len(clima) != 8760:
        raise ValueError("La serie climática debe tener 8760 horas.")

    energia_horaria: List[float] = []

    energia_anual = 0.0

    poa_total_kwh_m2 = 0.0

    # Potencia STC del generador
    potencia_dc_stc_kw = (panel.pmax_w * n_paneles) / 1000

    # Potencia AC máxima del inversor
    pac_nominal_w = pac_nominal_kw * 1000


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
        # IRRADIANCIA EN PLANO DEL GENERADOR (POA)
        # --------------------------------------------------

        poa = calcular_irradiancia_plano(

            ghi=hora_clima.ghi_wm2,

            zenith=pos.zenith,

            azimuth_solar=pos.azimuth,

            tilt=tilt,

            azimuth_superficie=azimuth

        )

        # Si no hay irradiancia no hay producción
        if poa <= 0:

            energia_horaria.append(0.0)

            continue

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

        p_dc_w = panel_real.pmp_w * n_paneles

        p_dc_w = max(p_dc_w, 0)


        # --------------------------------------------------
        # CONVERSIÓN A AC
        # --------------------------------------------------

        p_ac_w = p_dc_w * eficiencia_inversor


        # --------------------------------------------------
        # CLIPPING DEL INVERSOR
        # --------------------------------------------------

        if p_ac_w > pac_nominal_w:

            p_ac_w = pac_nominal_w


        # --------------------------------------------------
        # ENERGÍA HORARIA
        # --------------------------------------------------

        energia_kwh = p_ac_w / 1000

        energia_horaria.append(energia_kwh)

        energia_anual += energia_kwh


    # ======================================================
    # YIELD ESPECÍFICO
    # ======================================================

    if potencia_dc_stc_kw > 0:

        yield_especifico = energia_anual / potencia_dc_stc_kw

    else:

        yield_especifico = 0


    # ======================================================
    # PERFORMANCE RATIO
    # ======================================================

    if poa_total_kwh_m2 > 0:

        pr = energia_anual / (potencia_dc_stc_kw * poa_total_kwh_m2)

    else:

        pr = 0


    return ResultadoSimulacion8760(

        energia_horaria_kwh=energia_horaria,

        energia_anual_kwh=energia_anual,

        yield_especifico_kwh_kwp=yield_especifico,

        performance_ratio=pr,

        poa_total_kwh_m2=poa_total_kwh_m2

    )
