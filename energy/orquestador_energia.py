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

def _modelo_8760(inp: EnergiaInput):

    try:

        pdc = inp.pdc_instalada_kw
        pac = inp.pac_nominal_kw

        if pdc <= 0 or pac <= 0:
            raise ValueError("Potencias inválidas")

        produccion_especifica = 1600  # kWh/kWp/año Honduras

        energia_bruta_anual = pdc * produccion_especifica

        perdidas = (
            inp.perdidas_dc_pct +
            inp.perdidas_ac_pct +
            inp.sombras_pct
        ) / 100.0

        energia_util_anual = energia_bruta_anual * (1 - perdidas)

        dc_ac = pdc / pac

        clipping = max(0.0, (dc_ac - 1.2) * 0.05)

        energia_clipping_anual = energia_util_anual * clipping

        energia_final = energia_util_anual - energia_clipping_anual

        energia_bruta_12m = [energia_bruta_anual / 12] * 12
        energia_util_12m = [energia_final / 12] * 12
        energia_clipping_12m = [energia_clipping_anual / 12] * 12

        energia_perdidas_anual = energia_bruta_anual - energia_util_anual
        energia_perdidas_12m = [energia_perdidas_anual / 12] * 12

        energia_despues_perdidas_12m = [energia_util_anual / 12] * 12

        return EnergiaResultado(

            ok=True,
            errores=[],

            pdc_instalada_kw=pdc,
            pac_nominal_kw=pac,

            dc_ac_ratio=dc_ac,

            energia_bruta_12m=energia_bruta_12m,
            energia_perdidas_12m=energia_perdidas_12m,
            energia_despues_perdidas_12m=energia_despues_perdidas_12m,
            energia_clipping_12m=energia_clipping_12m,
            energia_util_12m=energia_util_12m,

            energia_bruta_anual=energia_bruta_anual,
            energia_perdidas_anual=energia_perdidas_anual,
            energia_despues_perdidas_anual=energia_util_anual,
            energia_clipping_anual=energia_clipping_anual,
            energia_util_anual=energia_final,

            meta={}
        )

    except Exception as e:

        return _resultado_error(inp, [str(e)])


# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

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

            resultado = _modelo_8760(inp)

            resultado.meta = {
                "motor": "8760",
                "horas": 8760
            }

            return resultado

        raise ValueError(f"Modo de simulación desconocido: {modo}")

    except Exception as e:

        return _resultado_error(inp, [str(e)])
