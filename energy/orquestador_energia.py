from __future__ import annotations

from typing import List

from energy.contrato import EnergiaInput
from energy.resultado_energia import EnergiaResultado
from energy.sistema.agregacion_8760 import agregar_energia_por_mes

# MODELOS
from energy.panel_energia.modelo_termico import (
    calcular_temperatura_celda, ModeloTermicoInput
)
from energy.panel_energia.potencia_panel import (
    calcular_potencia_panel, PotenciaPanelInput
)
from energy.panel_energia.potencia_string import (
    calcular_potencia_string, PotenciaStringInput
)
from energy.panel_energia.potencia_arreglo import (
    calcular_potencia_arreglo, PotenciaArregloInput
)

# 🔥 USAR TU ORQUESTADOR SOLAR
from energy.solar.orquestador_solar import ejecutar_solar
from energy.solar.entrada_solar import EntradaSolar

from energy.sistema.modelo_energetico_inversor import calcular_inversor, InversorInput
from energy.sistema.perdidas_fisicas import aplicar_perdidas_fisicas, PerdidasInput
from energy.sistema.perdidas_ac import aplicar_perdidas_ac, PerdidasACInput


# ==========================================================
# ERROR
# ==========================================================
def _resultado_error(inp: EnergiaInput, errores: List[str]) -> EnergiaResultado:
    return EnergiaResultado(
        ok=False,
        errores=errores,
        pdc_instalada_kw=inp.pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=0.0,
        energia_bruta_12m=[],
        energia_perdidas_12m=[],
        energia_despues_perdidas_12m=[],
        energia_clipping_12m=[],
        energia_util_12m=[],
        energia_bruta_anual=0.0,
        energia_perdidas_anual=0.0,
        energia_despues_perdidas_anual=0.0,
        energia_clipping_anual=0.0,
        energia_util_anual=0.0,
        energia_horaria_kwh=[],
        produccion_especifica_kwh_kwp=0.0,
        performance_ratio=0.0,
        meta={}
    )


# ==========================================================
# ORQUESTADOR
# ==========================================================
def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = inp.validar()
    if errores:
        return _resultado_error(inp, errores)

    try:

        # 🔥 VALIDACIÓN CRÍTICA (esto te faltaba)
        if not inp.clima or not inp.clima.horas:
            raise Exception("Clima vacío o no definido")

        horas = inp.clima.horas

        dc_bruta_kw: List[float] = []
        ac_sin_clipping_kw: List[float] = []
        ac_final_kw: List[float] = []
        clipping_kw: List[float] = []

        poa_total_kwh = 0.0

        for h in horas:

            # ==================================================
            # 🔥 USAR ORQUESTADOR SOLAR (NO DUPLICAR)
            # ==================================================
            solar = ejecutar_solar(
                EntradaSolar(
                    lat=inp.clima.latitud,
                    lon=inp.clima.longitud,
                    fecha_hora=h.timestamp,
                    dni_wm2=h.dni_wm2,
                    dhi_wm2=h.dhi_wm2,
                    ghi_wm2=h.ghi_wm2,
                    temp_amb_c=h.temp_amb_c,
                    tilt_deg=inp.tilt_deg,
                    azimuth_panel_deg=inp.azimut_deg
                )
            )

            poa = max(0.0, solar.poa_total_wm2)
            poa_total_kwh += poa / 1000.0
            print("DNI:", h.dni_wm2, "DHI:", h.dhi_wm2, "GHI:", h.ghi_wm2)
            print("POA:", poa)
            print("----------------------")
            # ==================================================
            # TÉRMICO
            # ==================================================
            t_cell = calcular_temperatura_celda(
                ModeloTermicoInput(
                    irradiancia_poa_wm2=poa,
                    temperatura_ambiente_c=h.temp_amb_c,
                    noct_c=inp.panel.noct_c
                )
            ).temperatura_celda_c

            # ==================================================
            # PANEL
            # ==================================================
            panel = calcular_potencia_panel(
                PotenciaPanelInput(
                    irradiancia_poa_wm2=poa,
                    temperatura_celda_c=t_cell,
                    p_panel_w=inp.panel.pmax_w,
                    vmp_panel_v=inp.panel.vmp_v,
                    voc_panel_v=inp.panel.voc_v,
                    imp_panel_a=inp.panel.imp_a,
                    isc_panel_a=inp.panel.isc_a,
                    coef_potencia=inp.panel.coef_potencia_pct_c / 100,
                    coef_vmp=inp.panel.coef_vmp_pct_c / 100,
                    coef_voc=inp.panel.coef_voc_pct_c / 100,
                )
            )

            # ==================================================
            # STRING
            # ==================================================
            string = calcular_potencia_string(
                PotenciaStringInput(
                    n_series=inp.n_series,
                    p_panel_w=panel.pmp_w,
                    vmp_panel_v=panel.vmp_v,
                    voc_panel_v=panel.voc_v,
                    imp_panel_a=panel.imp_a,
                    isc_panel_a=panel.isc_a,
                )
            )

            # ==================================================
            # ARRAY
            # ==================================================
            array = calcular_potencia_arreglo(
                PotenciaArregloInput(
                    n_strings_total=inp.n_strings,
                    vmp_string_v=string.vmp_string_v,
                    voc_string_v=string.voc_string_v,
                    imp_string_a=string.imp_string_a,
                    isc_string_a=string.isc_string_a,
                    potencia_string_w=string.potencia_string_w,
                )
            )

            # ==================================================
            # DC
            # ==================================================
            dc_bruta = array.potencia_array_w / 1000.0
            dc_bruta_kw.append(dc_bruta)

            dc_neta = aplicar_perdidas_fisicas(
                PerdidasInput(
                    potencia_kw=dc_bruta,
                    perdidas_dc_pct=inp.perdidas_dc_pct,
                    sombras_pct=inp.sombras_pct,
                )
            ).potencia_kw

            # ==================================================
            # INVERSOR
            # ==================================================
            inv = calcular_inversor(
                InversorInput(
                    potencia_dc_kw=dc_neta,
                    p_ac_nominal_kw=inp.pac_nominal_kw,
                    eficiencia_nominal=inp.eficiencia_inversor,
                )
            )

            # ==================================================
            # AC
            # ==================================================
            ac_sin_clip = aplicar_perdidas_ac(
                PerdidasACInput(
                    potencia_kw=inv.potencia_ac_sin_clip_kw,
                    perdidas_ac_frac=inp.perdidas_ac_pct
                )
            ).potencia_kw

            ac_final = aplicar_perdidas_ac(
                PerdidasACInput(
                    potencia_kw=inv.potencia_ac_kw,
                    perdidas_ac_frac=inp.perdidas_ac_pct
                )
            ).potencia_kw

            ac_sin_clipping_kw.append(ac_sin_clip)
            ac_final_kw.append(ac_final)
            clipping_kw.append(inv.clipping_kw)

        # ==================================================
        # AGREGACIÓN
        # ==================================================
        energia_bruta_12m = agregar_energia_por_mes(dc_bruta_kw)
        energia_despues_perdidas_12m = agregar_energia_por_mes(ac_sin_clipping_kw)
        ac_final_kwh = [p * 1.0 for p in ac_final_kw]  # convertir a energía
        energia_util_12m = agregar_energia_por_mes(ac_final_kwh)

        energia_clipping_12m = [
            d - u for d, u in zip(energia_despues_perdidas_12m, energia_util_12m)
        ]

        energia_perdidas_12m = [
            b - d for b, d in zip(energia_bruta_12m, energia_despues_perdidas_12m)
        ]

        energia_bruta_anual = sum(dc_bruta_kw)
        energia_despues_perdidas_anual = sum(ac_sin_clipping_kw)
        energia_util_anual = sum(ac_final_kwh)

        energia_clipping_anual = (
            energia_despues_perdidas_anual - energia_util_anual
        )

        energia_perdidas_anual = (
            energia_bruta_anual - energia_despues_perdidas_anual
        )

        performance_ratio = (
            energia_util_anual / (poa_total_kwh * inp.pdc_kw)
            if poa_total_kwh > 0 else 0.0
        )

        return EnergiaResultado(
            ok=True,
            errores=[],
            pdc_instalada_kw=inp.pdc_kw,
            pac_nominal_kw=inp.pac_nominal_kw,
            dc_ac_ratio=inp.pdc_kw / inp.pac_nominal_kw,
            energia_bruta_12m=energia_bruta_12m,
            energia_perdidas_12m=energia_perdidas_12m,
            energia_despues_perdidas_12m=energia_despues_perdidas_12m,
            energia_clipping_12m=energia_clipping_12m,
            energia_util_12m=energia_util_12m,
            energia_bruta_anual=energia_bruta_anual,
            energia_perdidas_anual=energia_perdidas_anual,
            energia_despues_perdidas_anual=energia_despues_perdidas_anual,
            energia_clipping_anual=energia_clipping_anual,
            energia_util_anual=energia_util_anual,
            energia_horaria_kwh=ac_final_kw,
            produccion_especifica_kwh_kwp=(
                energia_util_anual / inp.pdc_kw if inp.pdc_kw > 0 else 0.0
            ),
            performance_ratio=performance_ratio,
            meta={
                "modelo": "8760_fisico",
                "pipeline": "clima→solar→dc→ac",
            }
        )

    except Exception as e:
        print("energia_util_anual:", energia_util_anual)
        print("pdc_kw:", inp.pdc_kw)
        print("produccion_especifica:", energia_util_anual / inp.pdc_kw)
        print("poa_total_kwh:", poa_total_kwh)
        print("PR:", performance_ratio)
        print("====================================")
        return _resultado_error(inp, [str(e)])
