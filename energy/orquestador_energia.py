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
        return _resultado_error(inp, ["Se requiere clima para simulación 8760"])

    if inp.tilt_deg is None:
        return _resultado_error(inp, ["Se requiere tilt_deg"])

    try:

        st.success("Ejecutando modelo 8760")

        # ======================================================
        # 1. SOLAR (POA + TEMP)
        # ======================================================

        from energy.clima.simulacion_8760 import simular_clima_8760

        resultado_solar = simular_clima_8760(
            clima=inp.clima,
            tilt=inp.tilt_deg,
            azimuth=180
        )

        estado = resultado_solar.horas


        # ======================================================
        # 2. ARRAY DC
        # ======================================================

        from energy.sistema.modelo_array_8760 import (
            calcular_array_8760,
            Array8760Input,
        )

        array = calcular_array_8760(
            Array8760Input(
                estado_solar=estado,
                paneles_por_string=inp.paneles_por_string,
                strings_totales=inp.n_strings_total,
                pmax_stc_w=inp.pmax_stc_w,
                vmp_stc_v=inp.vmp_stc_v,
                voc_stc_v=inp.voc_stc_v,
                coef_pmax_pct_per_c=inp.coef_pmax_pct_per_c,
                coef_voc_pct_per_c=inp.coef_voc_pct_per_c,
                coef_vmp_pct_per_c=inp.coef_vmp_pct_per_c,
            )
        )

        potencia_dc = array.potencia_dc_kw


        # ======================================================
        # 3. PÉRDIDAS FÍSICAS (DC)
        # ======================================================

        from energy.sistema.perdidas_fisicas import (
            aplicar_perdidas_fisicas,
            PerdidasInput,
        )

        r_perdidas_dc = aplicar_perdidas_fisicas(
            PerdidasInput(
                potencia_kw=potencia_dc,
                perdidas_dc_pct=inp.perdidas_dc_pct,
                sombras_pct=inp.sombras_pct,
            )
        )

        potencia_dc_corr = r_perdidas_dc.potencia_kw


        # ======================================================
        # 4. INVERSOR (DC → AC + CLIPPING)
        # ======================================================

        from energy.sistema.modelo_energetico_inversor import (
            calcular_inversor_8760,
            Inversor8760Input,
        )

        inv = calcular_inversor_8760(
            Inversor8760Input(
                potencia_dc_kw=potencia_dc_corr,
                p_ac_nominal_kw=inp.pac_nominal_kw,
                eficiencia_nominal=inp.eficiencia_inversor,
            )
        )

        potencia_ac = inv.potencia_ac_kw
        clipping_kw = inv.clipping_kw


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
            energia_perdidas_12m=[0.0] * 12,
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
                "factor_perdidas_dc": r_perdidas_dc.factor_total,
                "factor_perdidas_ac": r_ac.factor_ac,
            }
        )

    except Exception as e:

        st.error("Error en motor energía")
        st.write(str(e))

        return _resultado_error(inp, [str(e)])
