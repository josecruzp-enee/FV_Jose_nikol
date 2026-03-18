from __future__ import annotations

from .contrato import EnergiaInput, EnergiaResultado

from .sistema.orientacion import factor_orientacion_total
from .sistema.generacion_bruta import calcular_energia_bruta_dc
from .sistema.perdidas_fisicas import aplicar_perdidas
from .sistema.perdidas_ac import aplicar_perdidas_ac

from .sistema.modelo_energetico_inversor import (
    calcular_energia_inversor,
    EnergiaInversorInput
)


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
# MODELO HSP
# ==========================================================

def _modelo_hsp(inp: EnergiaInput):

    factor_orientacion = factor_orientacion_total(
        tipo_superficie=inp.tipo_superficie,
        azimut_deg=inp.azimut_deg,
        azimut_a_deg=inp.azimut_a_deg,
        azimut_b_deg=inp.azimut_b_deg,
        reparto_pct_a=inp.reparto_pct_a,
        hemisferio=inp.hemisferio,
    )

    r_bruta = calcular_energia_bruta_dc(
        pdc_kw=inp.pdc_instalada_kw,
        hsp_12m=inp.hsp_12m,
        dias_mes=inp.dias_mes,
        factor_orientacion=factor_orientacion,
    )

    if not r_bruta.ok:
        return None, r_bruta.errores

    energia_bruta = r_bruta.energia_mensual_dc_kwh

    r_perdidas = aplicar_perdidas(
        energia_dc_12m=energia_bruta,
        perdidas_dc_pct=inp.perdidas_dc_pct,
        perdidas_ac_pct=0.0,
        sombras_pct=inp.sombras_pct,
    )

    if not r_perdidas.ok:
        return None, r_perdidas.errores

    energia_despues_perdidas_dc = r_perdidas.energia_neta_12m_kwh

    energia_perdidas = [
        b - d for b, d in zip(energia_bruta, energia_despues_perdidas_dc)
    ]

    inv_input = EnergiaInversorInput(

        energia_dc_12m_kwh=energia_despues_perdidas_dc,
        kw_ac=inp.pac_nominal_kw,
        pdc_kw=inp.pdc_instalada_kw,
        eficiencia_nominal=inp.eficiencia_inversor,
    )

    r_inv = calcular_energia_inversor(inv_input)

    energia_ac_pre = r_inv.energia_ac_12m_kwh
    energia_clipping = r_inv.energia_clipping_12m_kwh

    r_ac = aplicar_perdidas_ac(
        energia_ac_12m=energia_ac_pre,
        perdidas_ac_pct=inp.perdidas_ac_pct,
    )

    if not r_ac.ok:
        return None, r_ac.errores

    energia_util = r_ac.energia_final_12m_kwh

    energia_perdidas_ac = [
        a - b for a, b in zip(energia_ac_pre, energia_util)
    ]

    energia_perdidas = [
        dc + ac for dc, ac in zip(energia_perdidas, energia_perdidas_ac)
    ]

    return (
        energia_bruta,
        energia_perdidas,
        energia_despues_perdidas_dc,
        energia_util,
        energia_clipping,
        factor_orientacion,
    ), []


# ==========================================================
# MODELO 8760 (SIMPLIFICADO)
# ==========================================================

def _modelo_8760(inp: EnergiaInput) -> EnergiaResultado:

    try:

        # --------------------------------------------------
        # VALIDACIONES
        # --------------------------------------------------

        pdc = inp.pdc_instalada_kw
        pac = inp.pac_nominal_kw

        if pdc <= 0 or pac <= 0:
            raise ValueError("Potencias inválidas")

        if inp.clima is None:
            raise ValueError("No se proporcionó clima para simulación 8760")

        # --------------------------------------------------
        # IMPORTS (tus módulos reales)
        # --------------------------------------------------

        from energy.clima.simulador_8760 import simular_clima_8760
        from energy.sistema.agregacion_8760 import agregar_8760
        from energy.panel_energia.array_8760 import (
            calcular_array_8760,
            Array8760Input
        )
        from energy.sistema.modelo_energetico_inversor import (
            calcular_energia_inversor_horario
        )

        # --------------------------------------------------
        # 1. CLIMA 8760
        # --------------------------------------------------

        clima_8760 = simular_clima_8760(
            clima=inp.clima,
            tilt=inp.tilt_deg,
            azimuth=inp.azimut_deg
        )

        # --------------------------------------------------
        # 2. ARRAY DC (REAL)
        # --------------------------------------------------

        array = calcular_array_8760(

            Array8760Input(
                estado_solar=clima_8760.horas,

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

        energia_horaria = []
        clipping_horaria = []

        # --------------------------------------------------
        # 3. INVERSOR (HORARIO)
        # --------------------------------------------------

        for p_dc in potencia_dc:

            p_ac, clipping = calcular_energia_inversor_horario(
                p_dc_kw=p_dc,
                pac_kw=pac,
                eficiencia=inp.eficiencia_inversor
            )

            energia_horaria.append(p_ac)
            clipping_horaria.append(clipping)

        # --------------------------------------------------
        # 4. AGREGACIÓN
        # --------------------------------------------------

        agg = agregar_8760(
            energia_horaria=energia_horaria,
            clipping_horaria=clipping_horaria
        )

        energia_12m = agg["energia_12m"]
        clipping_12m = agg["clipping_12m"]
        energia_anual = agg["energia_anual"]
        clipping_anual = agg["clipping_anual"]

        # --------------------------------------------------
        # 5. PÉRDIDAS
        # --------------------------------------------------

        perdidas_pct = (
            inp.perdidas_dc_pct +
            inp.perdidas_ac_pct +
            inp.sombras_pct
        ) / 100.0

        energia_util_12m = [e * (1 - perdidas_pct) for e in energia_12m]
        energia_util_anual = energia_anual * (1 - perdidas_pct)

        energia_perdidas_12m = [
            e - u for e, u in zip(energia_12m, energia_util_12m)
        ]
        energia_perdidas_anual = energia_anual - energia_util_anual

        # --------------------------------------------------
        # RESULTADO FINAL
        # --------------------------------------------------

        return EnergiaResultado(

            ok=True,
            errores=[],

            pdc_instalada_kw=pdc,
            pac_nominal_kw=pac,

            dc_ac_ratio=pdc / pac,

            energia_bruta_12m=energia_12m,
            energia_perdidas_12m=energia_perdidas_12m,
            energia_despues_perdidas_12m=energia_util_12m,
            energia_clipping_12m=clipping_12m,
            energia_util_12m=energia_util_12m,

            energia_bruta_anual=energia_anual,
            energia_perdidas_anual=energia_perdidas_anual,
            energia_despues_perdidas_anual=energia_util_anual,
            energia_clipping_anual=clipping_anual,
            energia_util_anual=energia_util_anual,

            meta={
                "motor": "8760",
                "horas": 8760
            }
        )

    except Exception as e:

        return _resultado_error(inp, [str(e)])


# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:
    import streamlit as st

    st.warning("DEBUG MOTOR ENERGÍA")
    st.write("Modo solicitado:", inp.modo_simulacion)
    st.write("PDC:", inp.pdc_instalada_kw)
    st.write("PAC:", inp.pac_nominal_kw)

    errores: list[str] = []

    try:

        modo = inp.modo_simulacion

        # ==================================================
        # MOTOR HSP
        # ==================================================

        if modo == "mensual":

            data, errores = _modelo_hsp(inp)

            if errores:
                return _resultado_error(inp, errores)

            (
                energia_bruta,
                energia_perdidas,
                energia_despues_perdidas,
                energia_util,
                energia_clipping,
                factor_orientacion,
            ) = data

            return EnergiaResultado(

                ok=True,
                errores=[],

                pdc_instalada_kw=inp.pdc_instalada_kw,
                pac_nominal_kw=inp.pac_nominal_kw,

                dc_ac_ratio=inp.pdc_instalada_kw / inp.pac_nominal_kw,

                energia_bruta_12m=energia_bruta,
                energia_perdidas_12m=energia_perdidas,
                energia_despues_perdidas_12m=energia_despues_perdidas,
                energia_clipping_12m=energia_clipping,
                energia_util_12m=energia_util,

                energia_bruta_anual=sum(energia_bruta),
                energia_perdidas_anual=sum(energia_perdidas),
                energia_despues_perdidas_anual=sum(energia_despues_perdidas),
                energia_clipping_anual=sum(energia_clipping),
                energia_util_anual=sum(energia_util),

                meta={
                    "motor": "mensual",
                    "meses": 12,
                    "factor_orientacion": factor_orientacion,
                },
            )

        # ==================================================
        # MOTOR 8760
        # ==================================================

        if modo == "8760":
            st.success("ENTRÓ A 8760")
            st.write("Modo solicitado:", inp.modo_simulacion)
            resultado = _modelo_8760(inp)

            resultado.meta = {
                "motor": "8760",
                "horas": 8760
            }

            return resultado

        raise ValueError(f"Modo de simulación desconocido: {modo}")

    except Exception as e:

        return _resultado_error(inp, [str(e)])
