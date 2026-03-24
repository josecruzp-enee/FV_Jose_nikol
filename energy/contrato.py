from __future__ import annotations

from dataclasses import dataclass
from typing import List

from energy.contrato import EnergiaResultado, EnergiaInput
from energy.sistema.agregacion_8760 import agregar_energia_por_mes


# ==========================================================
# RESULTADO ERROR
# ==========================================================
def _resultado_error(inp, errores):

    paneles = inp.paneles

    pdc_kw = 0.0
    if paneles and hasattr(paneles, "array"):
        pdc_kw = paneles.array.potencia_dc_w / 1000

    return EnergiaResultado(
        ok=False,
        errores=errores,

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=0.0,

        energia_horaria_kwh=[],

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

        produccion_especifica_kwh_kwp=0.0,
        performance_ratio=0.0,

        meta={}
    )


# ==========================================================
# CLIMA
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
# DC FÍSICO 8760 (🔥 NUEVO)
# ==========================================================
def _calcular_dc_8760_fisico(inp: EnergiaInput, estados):

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

    resultados = []

    panel = inp.panel
    arreglo = inp.paneles.array

    for estado in estados:

        poa = estado.poa_wm2
        tamb = estado.temp_amb_c

        # ----------------------------------
        # 1. TEMPERATURA CELDA
        # ----------------------------------
        t_cell = calcular_temperatura_celda(
            ModeloTermicoInput(
                irradiancia_poa_wm2=poa,
                temperatura_ambiente_c=tamb,
                noct_c=panel.noct,
            )
        ).temperatura_celda_c

        # ----------------------------------
        # 2. PANEL
        # ----------------------------------
        p = calcular_potencia_panel(
            PotenciaPanelInput(
                irradiancia_poa_wm2=poa,
                temperatura_celda_c=t_cell,

                p_panel_w=panel.p_nom,
                vmp_panel_v=panel.vmp,
                voc_panel_v=panel.voc,
                imp_panel_a=panel.imp,
                isc_panel_a=panel.isc,

                coef_potencia=panel.gamma_p,
                coef_vmp=panel.gamma_vmp,
                coef_voc=panel.gamma_voc,
            )
        )

        # ----------------------------------
        # 3. STRING
        # ----------------------------------
        n_series = arreglo.n_paneles_total // arreglo.n_strings_total

        string = calcular_potencia_string(
            PotenciaStringInput(
                n_series=n_series,

                p_panel_w=p.pmp_w,
                vmp_panel_v=p.vmp_v,
                voc_panel_v=p.voc_v,
                imp_panel_a=p.imp_a,
                isc_panel_a=p.isc_a,
            )
        )

        # ----------------------------------
        # 4. ARREGLO
        # ----------------------------------
        array = calcular_potencia_arreglo(
            PotenciaArregloInput(
                n_strings_total=arreglo.n_strings_total,

                vmp_string_v=string.vmp_string_v,
                voc_string_v=string.voc_string_v,
                imp_string_a=string.imp_string_a,
                isc_string_a=string.isc_string_a,
                potencia_string_w=string.potencia_string_w,
            )
        )

        resultados.append(array.potencia_array_w / 1000.0)

    return resultados


# ==========================================================
# PÉRDIDAS DC
# ==========================================================
def _aplicar_perdidas_dc(inp: EnergiaInput, potencia_dc_kw):

    from energy.sistema.perdidas_fisicas import (
        aplicar_perdidas_fisicas, PerdidasInput
    )

    base = aplicar_perdidas_fisicas(
        PerdidasInput(
            potencia_kw=potencia_dc_kw,
            perdidas_dc_pct=inp.perdidas_dc_pct,
            sombras_pct=inp.sombras_pct,
        )
    )

    potencia_neta = base.potencia_kw

    perdidas = [
        p_in - p_out
        for p_in, p_out in zip(potencia_dc_kw, potencia_neta)
    ]

    return potencia_neta, perdidas


# ==========================================================
# INVERSOR
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
# PÉRDIDAS AC
# ==========================================================
def _aplicar_perdidas_ac(inp: EnergiaInput, potencia_ac_kw):

    from energy.sistema.perdidas_ac import (
        aplicar_perdidas_ac, PerdidasACInput
    )

    base = aplicar_perdidas_ac(
        PerdidasACInput(
            potencia_kw=potencia_ac_kw,
            perdidas_ac_pct=inp.perdidas_ac_pct,
        )
    )

    potencia_neta = base.potencia_kw

    perdidas = [
        p_in - p_out
        for p_in, p_out in zip(potencia_ac_kw, potencia_neta)
    ]

    return potencia_neta, perdidas


# ==========================================================
# RESULTADO
# ==========================================================
def _construir_resultado(
    inp,
    dc_bruta_kw,
    ac_neta_kw,
    clipping_kw,
):

    energia_bruta_12m = agregar_energia_por_mes(dc_bruta_kw)
    energia_final_12m = agregar_energia_por_mes(ac_neta_kw)
    energia_clipping_12m = agregar_energia_por_mes(clipping_kw)

    energia_bruta_anual = sum(dc_bruta_kw)
    energia_final_anual = sum(ac_neta_kw)
    energia_clipping_anual = sum(clipping_kw)

    pdc_kw = inp.paneles.array.potencia_dc_w / 1000

    produccion_especifica_kwh_kwp = (
        energia_final_anual / pdc_kw if pdc_kw > 0 else 0.0
    )

    performance_ratio = (
        energia_final_anual / energia_bruta_anual
        if energia_bruta_anual > 0 else 0.0
    )

    return EnergiaResultado(
        ok=True,
        errores=[],

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=pdc_kw / inp.pac_nominal_kw if inp.pac_nominal_kw else 0.0,

        energia_horaria_kwh=ac_neta_kw,

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

        produccion_especifica_kwh_kwp=produccion_especifica_kwh_kwp,
        performance_ratio=performance_ratio,

        meta={"motor": "8760_fisico"},
    )


# ==========================================================
# MAIN
# ==========================================================
def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = inp.validar()
    if errores:
        return _resultado_error(inp, errores)

    estados = _simular_estado_8760(inp)

    # 🔥 NUEVO MOTOR DC
    dc_bruta = _calcular_dc_8760_fisico(inp, estados)

    dc_neta, _ = _aplicar_perdidas_dc(inp, dc_bruta)

    inv = _aplicar_inversor(inp, dc_neta)

    ac_neta, _ = _aplicar_perdidas_ac(inp, inv.potencia_ac_kw)

    return _construir_resultado(
        inp=inp,
        dc_bruta_kw=dc_bruta,
        ac_neta_kw=ac_neta,
        clipping_kw=inv.clipping_kw,
    )
