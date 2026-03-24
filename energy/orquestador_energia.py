from __future__ import annotations

from typing import List

from energy.contrato import EnergiaInput, EnergiaResultado
from energy.sistema.agregacion_8760 import agregar_energia_por_mes

# 🔥 MODELOS UNITARIOS (LOS TUYOS)
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

# 🔥 SOLAR
from energy.solar.posicion_solar import calcular_posicion_solar, SolarInput
from energy.solar.irradiancia_plano import calcular_irradiancia_plano, IrradianciaInput

# 🔥 SISTEMA
from energy.sistema.perdidas_fisicas import aplicar_perdidas_fisicas, PerdidasInput
from energy.sistema.modelo_energetico_inversor import (
    calcular_inversor_8760, Inversor8760Input
)
from energy.sistema.perdidas_ac import aplicar_perdidas_ac, PerdidasACInput


# ==========================================================
# RESULTADO ERROR
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
# ORQUESTADOR 8760 REAL
# ==========================================================
def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = inp.validar()
    if errores:
        return _resultado_error(inp, errores)

    try:

        horas = inp.clima.horas  # 8760

        dc_bruta_kw: List[float] = []
        ac_kw: List[float] = []
        ac_final_kw: List[float] = []
        clipping_kw: List[float] = []

        poa_total_kwh = 0.0  # para PR correcto

        # ==================================================
        # LOOP 8760 (UNITARIO REAL)
        # ==================================================
        for h in horas:

            # ----------------------------------------------
            # 1. POSICIÓN SOLAR
            # ----------------------------------------------
            pos = calcular_posicion_solar(
                SolarInput(
                    latitud_deg=inp.clima.latitud,
                    longitud_deg=inp.clima.longitud,
                    fecha_hora=h.timestamp
                )
            )

            # ----------------------------------------------
            # 2. POA
            # ----------------------------------------------
            irr = calcular_irradiancia_plano(
                IrradianciaInput(
                    dni=h.dni_wm2,
                    dhi=h.dhi_wm2,
                    ghi=h.ghi_wm2,
                    solar_zenith_deg=pos.zenith_deg,
                    solar_azimuth_deg=pos.azimuth_deg,
                    panel_tilt_deg=inp.tilt_deg,
                    panel_azimuth_deg=inp.azimut_deg
                )
            )

            poa = max(0.0, irr.poa_total)
            poa_total_kwh += poa / 1000.0

            # ----------------------------------------------
            # 3. TEMPERATURA DE CELDA
            # ----------------------------------------------
            t_cell = calcular_temperatura_celda(
                ModeloTermicoInput(
                    irradiancia_poa_wm2=poa,
                    temperatura_ambiente_c=h.temp_amb_c,
                    noct_c=inp.panel.noct_c
                )
            ).temperatura_celda_c

            # ----------------------------------------------
            # 4. PANEL
            # ----------------------------------------------
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

            # ----------------------------------------------
            # 5. STRING
            # ----------------------------------------------
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

            # ----------------------------------------------
            # 6. ARRAY
            # ----------------------------------------------
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

            # ----------------------------------------------
            # 7. DC BRUTA (kW)
            # ----------------------------------------------
            dc_bruta_h = array.potencia_array_w / 1000.0
            dc_bruta_kw.append(dc_bruta_h)

            # ----------------------------------------------
            # 8. PÉRDIDAS DC (unitario)
            # ----------------------------------------------
            dc_neta_h = dc_bruta_h * (1 - inp.perdidas_dc_pct) * (1 - inp.sombras_pct)

            # ----------------------------------------------
            # 9. INVERSOR (unitario)
            # ----------------------------------------------
            inv = calcular_inversor(
                InversorInput(
                    potencia_dc_kw=dc_neta_h,
                    p_ac_nominal_kw=inp.pac_nominal_kw,
                    eficiencia_nominal=inp.eficiencia_inversor,
                )
            )

            ac_h = inv.potencia_ac_kw
            ac_kw.append(ac_h)
            clipping_kw.append(inv.clipping_kw)

            # ----------------------------------------------
            # 10. PÉRDIDAS AC (unitario)
            # ----------------------------------------------
            ac_final_h = ac_h * (1 - inp.perdidas_ac_pct)
            ac_final_kw.append(ac_final_h)

        # ==================================================
        # AGREGACIÓN
        # ==================================================
        energia_bruta_12m = agregar_energia_por_mes(dc_bruta_kw)
        energia_util_12m = agregar_energia_por_mes(ac_final_kw)
        energia_clipping_12m = agregar_energia_por_mes(clipping_kw)

        energia_bruta_anual = sum(dc_bruta_kw)
        energia_util_anual = sum(ac_final_kw)
        energia_clipping_anual = sum(clipping_kw)

        # ==================================================
        # PR CORRECTO
        # ==================================================
        performance_ratio = (
            energia_util_anual /
            (poa_total_kwh * inp.pdc_kw)
            if poa_total_kwh > 0 else 0.0
        )

        # ==================================================
        # RESULTADO FINAL
        # ==================================================
        return EnergiaResultado(
            ok=True,
            errores=[],

            pdc_instalada_kw=inp.pdc_kw,
            pac_nominal_kw=inp.pac_nominal_kw,
            dc_ac_ratio=inp.pdc_kw / inp.pac_nominal_kw,

            energia_bruta_12m=energia_bruta_12m,
            energia_perdidas_12m=[
                b - u for b, u in zip(energia_bruta_12m, energia_util_12m)
            ],
            energia_despues_perdidas_12m=energia_util_12m,
            energia_clipping_12m=energia_clipping_12m,
            energia_util_12m=energia_util_12m,

            energia_bruta_anual=energia_bruta_anual,
            energia_perdidas_anual=energia_bruta_anual - energia_util_anual,
            energia_despues_perdidas_anual=energia_util_anual,
            energia_clipping_anual=energia_clipping_anual,
            energia_util_anual=energia_util_anual,

            energia_horaria_kwh=ac_final_kw,

            produccion_especifica_kwh_kwp=(
                energia_util_anual / inp.pdc_kw if inp.pdc_kw > 0 else 0.0
            ),

            performance_ratio=performance_ratio,

            meta={
                "modelo": "8760_real_unitario",
                "pipeline": "clima→poa→temp→panel→string→array→dc→inv→ac"
            }
        )

    except Exception as e:
        return _resultado_error(inp, [str(e)])
