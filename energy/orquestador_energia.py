from __future__ import annotations

from .contrato import EnergiaInput, EnergiaResultado
from energy.sistema.agregacion_8760 import agregar_energia_por_mes

import streamlit as st


# ==========================================================
# ERROR
# ==========================================================

def _resultado_error(inp: EnergiaInput, errores: list[str]) -> EnergiaResultado:

    pdc_kw = inp.paneles.array.potencia_dc_w / 1000 if inp.paneles else 0.0

    return EnergiaResultado(
        ok=False,
        errores=errores,

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=0.0,

        energia_horaria=[],

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

        meta={"estado": "error"},
    )


# ==========================================================
# 1. CLIMA + SOLAR
# ==========================================================

def _simular_estado_8760(inp: EnergiaInput):

    from energy.clima.simulacion_8760 import simular_clima_8760

    resultado = simular_clima_8760(
        clima=inp.clima,
        tilt=inp.tilt_deg,
        azimuth=inp.azimut_deg,
    )

    return resultado.horas


# ==========================================================
# 2. DC
# ==========================================================

def _calcular_dc(inp: EnergiaInput, estado):

    from energy.panel_energia.modelo_termico import (
        calcular_temperatura_celda, ModeloTermicoInput
    )
    from energy.panel_energia.potencia_panel import (
        calcular_potencia_panel, PotenciaPanelInput
    )

    paneles = inp.paneles
    array = paneles.array
    string = paneles.strings[0]

    potencia_dc_kw = []

    for hora in estado:

        if hora.poa_wm2 <= 0:
            potencia_dc_kw.append(0.0)
            continue

        # térmico
        t_cell = calcular_temperatura_celda(
            ModeloTermicoInput(
                irradiancia_poa_wm2=hora.poa_wm2,
                temperatura_ambiente_c=hora.temp_amb_c,
                noct_c=45.0,
            )
        ).temperatura_celda_c

        # panel
        panel = calcular_potencia_panel(
            PotenciaPanelInput(
                irradiancia_poa_wm2=hora.poa_wm2,
                temperatura_celda_c=t_cell,

                p_panel_w=array.p_panel_w,
                vmp_panel_v=string.vmp_string_v / string.n_series,
                voc_panel_v=string.voc_frio_string_v / string.n_series,

                imp_panel_a=string.imp_string_a,
                isc_panel_a=string.isc_string_a,

                coef_potencia=array.coef_potencia,
                coef_vmp=array.coef_vmp,
                coef_voc=array.coef_voc,
            )
        )

        p_array_w = panel.pmp_w * array.n_paneles_total

        potencia_dc_kw.append(p_array_w / 1000.0)

    return potencia_dc_kw


# ==========================================================
# 3. PÉRDIDAS DC
# ==========================================================

def _aplicar_perdidas_dc(inp: EnergiaInput, potencia_dc_kw):

    from energy.sistema.perdidas_fisicas import (
        aplicar_perdidas_fisicas, PerdidasInput
    )

    return aplicar_perdidas_fisicas(
        PerdidasInput(
            potencia_kw=potencia_dc_kw,
            perdidas_dc_pct=inp.perdidas_dc_pct,
            sombras_pct=inp.sombras_pct,
        )
    )


# ==========================================================
# 4. INVERSOR
# ==========================================================

def _aplicar_inversor(inp: EnergiaInput, potencia_dc_kw):

    from energy.sistema.modelo_energetico_inversor import (
        calcular_inversor_8760, Inversor8760Input
    )

    return calcular_inversor_8760(
        Inversor8760Input(
            potencia_dc_kw=potencia_dc_kw,
            p_ac_nominal_kw=inp.pac_nominal_kw,
            eficiencia_nominal=inp.eficiencia_inversor,
        )
    )


# ==========================================================
# 5. PÉRDIDAS AC
# ==========================================================

def _aplicar_perdidas_ac(inp: EnergiaInput, potencia_ac_kw):

    from energy.sistema.perdidas_ac import (
        aplicar_perdidas_ac, PerdidasACInput
    )

    return aplicar_perdidas_ac(
        PerdidasACInput(
            potencia_kw=potencia_ac_kw,
            perdidas_ac_pct=inp.perdidas_ac_pct,
        )
    )


# ==========================================================
# 6. RESULTADO
# ==========================================================

def _construir_resultado(inp, potencia_dc_kw, potencia_ac_kw, clipping_kw):

    energia_bruta_12m = agregar_energia_por_mes(potencia_dc_kw)
    energia_final_12m = agregar_energia_por_mes(potencia_ac_kw)
    energia_clipping_12m = agregar_energia_por_mes(clipping_kw)

    energia_bruta_anual = sum(potencia_dc_kw)
    energia_final_anual = sum(potencia_ac_kw)
    energia_clipping_anual = sum(clipping_kw)

    pdc_kw = inp.paneles.array.potencia_dc_w / 1000

    return EnergiaResultado(
        ok=True,
        errores=[],

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=pdc_kw / inp.pac_nominal_kw,

        energia_horaria=[],

        energia_bruta_12m=energia_bruta_12m,
        energia_perdidas_12m=[b - f for b, f in zip(energia_bruta_12m, energia_final_12m)],
        energia_despues_perdidas_12m=energia_final_12m,
        energia_clipping_12m=energia_clipping_12m,
        energia_util_12m=energia_final_12m,

        energia_bruta_anual=energia_bruta_anual,
        energia_perdidas_anual=energia_bruta_anual - energia_final_anual,
        energia_despues_perdidas_anual=energia_final_anual,
        energia_clipping_anual=energia_clipping_anual,
        energia_util_anual=energia_final_anual,

        meta={"motor": "8760"},
    )


# ==========================================================
# MAIN
# ==========================================================

def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = inp.validar()
    if errores:
        return _resultado_error(inp, errores)

    estado = _simular_estado_8760(inp)

    potencia_dc = _calcular_dc(inp, estado)

    r_dc = _aplicar_perdidas_dc(inp, potencia_dc)

    inv = _aplicar_inversor(inp, r_dc.potencia_kw)

    r_ac = _aplicar_perdidas_ac(inp, inv.potencia_ac_kw)

    return _construir_resultado(
        inp,
        potencia_dc,
        r_ac.potencia_kw,
        inv.clipping_kw,
    )
