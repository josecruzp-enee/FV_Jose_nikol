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

    # ------------------------------------------------------
    # ORIENTACIÓN
    # ------------------------------------------------------

    factor_orientacion = factor_orientacion_total(

        tipo_superficie=inp.tipo_superficie,
        azimut_deg=inp.azimut_deg,
        azimut_a_deg=inp.azimut_a_deg,
        azimut_b_deg=inp.azimut_b_deg,
        reparto_pct_a=inp.reparto_pct_a,
        hemisferio=inp.hemisferio,
    )

    # ------------------------------------------------------
    # GENERACIÓN DC BRUTA
    # ------------------------------------------------------

    r_bruta = calcular_energia_bruta_dc(
        pdc_kw=inp.pdc_instalada_kw,
        hsp_12m=inp.hsp_12m,
        dias_mes=inp.dias_mes,
        factor_orientacion=factor_orientacion,
    )

    if not r_bruta.ok:
        return None, r_bruta.errores

    energia_bruta = r_bruta.energia_mensual_dc_kwh

    # ------------------------------------------------------
    # PÉRDIDAS DC + SOMBRAS
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # INVERSOR
    # ------------------------------------------------------

    inv_input = EnergiaInversorInput(

        energia_dc_12m_kwh=energia_despues_perdidas_dc,

        kw_ac=inp.pac_nominal_kw,

        pdc_kw=inp.pdc_instalada_kw,

        eficiencia_nominal=inp.eficiencia_inversor,
    )

    r_inv = calcular_energia_inversor(inv_input)

    energia_ac_pre = r_inv.energia_ac_12m_kwh
    energia_clipping = r_inv.energia_clipping_12m_kwh

    # ------------------------------------------------------
    # PÉRDIDAS AC
    # ------------------------------------------------------

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
# MOTOR PRINCIPAL
# ==========================================================

def ejecutar_motor_energia(inp):

    """
    Orquestador del motor energético FV.

    Permite ejecutar dos modos:

        • HSP mensual (rápido)
        • simulación 8760 (preciso)
    """

    errores = []

    try:

        # ==================================================
        # SELECCIÓN DEL MOTOR
        # ==================================================

        modo = getattr(inp, "modo_motor", "mensual")

        # ==================================================
        # MOTOR HSP MENSUAL
        # ==================================================

        if modo == "mensual":

            resultado, errores = _modelo_hsp(inp)

            resultado.meta = {

                "motor": "mensual",
                "meses": 12,
                "factor_orientacion": getattr(inp, "factor_orientacion", 1.0)

            }

            return resultado

        # ==================================================
        # MOTOR 8760 HORARIO
        # ==================================================

        if modo == "8760":

            resultado, errores = _modelo_8760(inp)

            resultado.meta = {

                "motor": "8760",
                "horas": 8760

            }

            return resultado

        # ==================================================
        # MOTOR DESCONOCIDO
        # ==================================================

        raise ValueError(f"Modo de simulación desconocido: {modo}")

    except Exception as e:

        errores.append(str(e))

        from energy.contrato import EnergiaResultado

        return EnergiaResultado(

            ok=False,
            errores=errores,
            pdc_instalada_kw=0,
            pac_nominal_kw=0,
            dc_ac_ratio=0,

            energia_bruta_12m=[],
            energia_perdidas_12m=[],
            energia_despues_perdidas_12m=[],
            energia_clipping_12m=[],
            energia_util_12m=[],

            energia_bruta_anual=0,
            energia_perdidas_anual=0,
            energia_despues_perdidas_anual=0,
            energia_clipping_anual=0,
            energia_util_anual=0,

            meta={}
        )
