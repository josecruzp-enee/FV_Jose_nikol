from __future__ import annotations

from .contrato import EnergiaInput, EnergiaResultado

from energy.sistema.agregacion_8760 import agregar_energia_por_mes

import streamlit as st


# ==========================================================
# RESULTADO ERROR
# ==========================================================

def _resultado_error(inp: EnergiaInput, errores: list[str]) -> EnergiaResultado:

    return EnergiaResultado(
        ok=False,
        errores=errores,
        pdc_instalada_kw=inp.pdc_instalada_kw,
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
        meta={"estado": "error"},
    )


# ==========================================================
# ORQUESTADOR PRINCIPAL (SOLO 8760)
# ==========================================================

def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = inp.validar()
    if errores:
        return _resultado_error(inp, errores)

    if inp.clima is None:
        return _resultado_error(inp, ["Se requiere clima para 8760"])

    if inp.tilt_deg is None:
        return _resultado_error(inp, ["Se requiere tilt_deg"])

    try:

        st.success("Ejecutando modelo 8760")

        # ======================================================
        # 1. CLIMA + SOLAR
        # ======================================================

        from energy.clima.simulacion_8760 import simular_clima_8760

        resultado_solar = simular_clima_8760(
            clima=inp.clima,
            tilt=inp.tilt_deg,
            azimuth=180
        )

        estado = resultado_solar.horas


        # ======================================================
# 2. DC (USANDO panel_energia COMPLETO)
# ======================================================

from energy.panel_energia.modelo_termico import (
    calcular_temperatura_celda,
    ModeloTermicoInput,
)

from energy.panel_energia.potencia_panel import (
    calcular_potencia_panel,
    PotenciaPanelInput,
)

from energy.panel_energia.potencia_string import (
    calcular_potencia_string,
    PotenciaStringInput,
)

from energy.panel_energia.potencia_arreglo import (
    calcular_potencia_arreglo,
    PotenciaArregloInput,
)

potencia_dc = []

for hora in estado:

    if hora.poa_wm2 <= 0:
        potencia_dc.append(0.0)
        continue

    # --------------------------------------------------
    # 1. TEMPERATURA DE CELDA
    # --------------------------------------------------

    t_cell = calcular_temperatura_celda(
        ModeloTermicoInput(
            irradiancia_poa_wm2=hora.poa_wm2,
            temperatura_ambiente_c=hora.temp_ambiente_c,
            noct_c=inp.noct_c,
        )
    ).temperatura_celda_c

    # --------------------------------------------------
    # 2. PANEL
    # --------------------------------------------------

    panel = calcular_potencia_panel(
        PotenciaPanelInput(
            irradiancia_poa_wm2=hora.poa_wm2,
            temperatura_celda_c=t_cell,

            p_panel_w=inp.p_panel_w,

            vmp_panel_v=inp.vmp_panel_v,
            voc_panel_v=inp.voc_panel_v,

            imp_panel_a=inp.imp_panel_a,
            isc_panel_a=inp.isc_panel_a,

            coef_potencia=inp.coef_potencia,
            coef_vmp=inp.coef_vmp,
            coef_voc=inp.coef_voc,
        )
    )

    # --------------------------------------------------
    # 3. STRING (SERIE)
    # --------------------------------------------------

    string = calcular_potencia_string(
        PotenciaStringInput(
            n_series=inp.paneles_por_string,

            p_panel_w=panel.pmp_w,

            vmp_panel_v=panel.vmp_v,
            voc_panel_v=panel.voc_v,

            imp_panel_a=panel.imp_a,
            isc_panel_a=panel.isc_a,
        )
    )

    # --------------------------------------------------
    # 4. ARREGLO (PARALELO)
    # --------------------------------------------------

    array = calcular_potencia_arreglo(
        PotenciaArregloInput(
            n_strings_total=inp.n_strings_total,

            vmp_string_v=string.vmp_string_v,
            voc_string_v=string.voc_string_v,

            imp_string_a=string.imp_string_a,
            isc_string_a=string.isc_string_a,

            potencia_string_w=string.potencia_string_w,
        )
    )

    # --------------------------------------------------
    # 5. RESULTADO kW
    # --------------------------------------------------

    potencia_dc.append(max(0.0, array.potencia_array_w / 1000.0))

        # ======================================================
        # 3. PÉRDIDAS DC
        # ======================================================

        from energy.sistema.perdidas_fisicas import (
            aplicar_perdidas_fisicas,
            PerdidasInput,
        )

        r_dc = aplicar_perdidas_fisicas(
            PerdidasInput(
                potencia_kw=potencia_dc,
                perdidas_dc_pct=inp.perdidas_dc_pct,
                sombras_pct=inp.sombras_pct,
            )
        )

        potencia_dc_corr = r_dc.potencia_kw


        # ======================================================
        # 4. INVERSOR (CLIPPING REAL)
        # ======================================================

        from energy.sistema.modelo_energetico_inversor import (
            calcular_inversor_8760,
        )

        inv = calcular_inversor_8760(
            potencia_dc_kw_8760=potencia_dc_corr,
            p_ac_nominal_kw=inp.pac_nominal_kw,
            eficiencia_nominal=inp.eficiencia_inversor,
        )

        potencia_ac = inv["potencia_ac_kw_8760"]
        clipping_kw = inv["clipping_kw_8760"]


        # ======================================================
        # 5. PÉRDIDAS AC
        # ======================================================

        from energy.sistema.perdidas_ac import (
            aplicar_perdidas_ac,
            PerdidasACInput,
        )

        r_ac = aplicar_perdidas_ac(
            PerdidasACInput(
                potencia_kw=potencia_ac,
                perdidas_ac_pct=inp.perdidas_ac_pct,
            )
        )

        potencia_ac_final = r_ac.potencia_kw


        # ======================================================
        # 6. NORMALIZAR
        # ======================================================

        if len(potencia_ac_final) == 8784:
            potencia_ac_final = potencia_ac_final[:8760]
            clipping_kw = clipping_kw[:8760]


        # ======================================================
        # 7. AGREGACIÓN
        # ======================================================

        energia_mensual = agregar_energia_por_mes(potencia_ac_final)
        energia_anual = sum(potencia_ac_final)

        energia_clipping_12m = agregar_energia_por_mes(clipping_kw)
        energia_clipping_anual = sum(clipping_kw)


        # ======================================================
        # 8. SALIDA
        # ======================================================

        return EnergiaResultado(
            ok=True,
            errores=[],

            pdc_instalada_kw=inp.pdc_instalada_kw,
            pac_nominal_kw=inp.pac_nominal_kw,
            dc_ac_ratio=inp.pdc_instalada_kw / inp.pac_nominal_kw,

            energia_bruta_12m=energia_mensual,
            energia_perdidas_12m=[0.0]*12,
            energia_despues_perdidas_12m=energia_mensual,
            energia_clipping_12m=energia_clipping_12m,
            energia_util_12m=energia_mensual,

            energia_bruta_anual=energia_anual,
            energia_perdidas_anual=0.0,
            energia_despues_perdidas_anual=energia_anual,
            energia_clipping_anual=energia_clipping_anual,
            energia_util_anual=energia_anual,

            meta={
                "motor": "8760",
                "horas": 8760,
                "factor_perdidas_dc": r_dc.factor_total,
                "factor_perdidas_ac": r_ac.factor_ac,
            }
        )

    except Exception as e:

        st.error("Error en motor energía")
        st.write(str(e))

        return _resultado_error(inp, [str(e)])
