from __future__ import annotations

from .contrato import EnergiaInput, EnergiaResultado

from .generacion_bruta import calcular_energia_bruta_dc
from .perdidas_fisicas import aplicar_perdidas
from .limitacion_inversor import aplicar_curtailment

# motor avanzado
from .clima.simulacion_8760 import simular_8760
from .clima.agregacion_8760 import agregar_energia_por_mes


# ==========================================================
# ERROR
# ==========================================================

def _resultado_error(inp: EnergiaInput, errores: list[str]) -> EnergiaResultado:

    return EnergiaResultado(
        ok=False,
        errores=errores,
        pdc_instalada_kw=inp.pdc_instalada_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=0.0,
        energia_bruta_12m=[],
        energia_despues_perdidas_12m=[],
        energia_curtailment_12m=[],
        energia_util_12m=[],
        energia_bruta_anual=0.0,
        energia_util_anual=0.0,
        energia_curtailment_anual=0.0,
        meta={"estado": "error"},
    )


# ==========================================================
# MODELO HSP (ACTUAL)
# ==========================================================

def _modelo_hsp(inp: EnergiaInput):

    r_bruta = calcular_energia_bruta_dc(
        pdc_kw=inp.pdc_instalada_kw,
        hsp_12m=inp.hsp_12m,
        dias_mes=inp.dias_mes,
        factor_orientacion=inp.factor_orientacion,
    )

    if not r_bruta.ok:
        return None, r_bruta.errores

    energia_bruta = r_bruta.energia_mensual_dc_kwh

    r_perdidas = aplicar_perdidas(
        energia_dc_12m=energia_bruta,
        perdidas_dc_pct=inp.perdidas_dc_pct,
        perdidas_ac_pct=inp.perdidas_ac_pct,
        sombras_pct=inp.sombras_pct,
    )

    if not r_perdidas.ok:
        return None, r_perdidas.errores

    energia_perdidas = r_perdidas.energia_neta_12m_kwh

    r_curt = aplicar_curtailment(
        energia_12m=energia_perdidas,
        pdc_kw=inp.pdc_instalada_kw,
        kw_ac=inp.pac_nominal_kw,
        permitir=inp.permitir_curtailment,
    )

    if not r_curt.ok:
        return None, r_curt.errores

    return (
        energia_bruta,
        energia_perdidas,
        r_curt.energia_final_12m_kwh,
        r_curt.energia_recortada_12m_kwh,
    ), []


# ==========================================================
# MODELO 8760
# ==========================================================

def _modelo_8760(inp: EnergiaInput):

    sim = ejecutar_simulacion_8760(inp)

    if not sim.ok:
        return None, sim.errores

    energia_horas = sim.potencia_ac_horaria_kw

    energia_mensual = agregar_energia_por_mes(energia_horas)

    return (
        energia_mensual,
        energia_mensual,
        energia_mensual,
        [0]*12,
    ), []


# ==========================================================
# MOTOR ENERGÉTICO
# ==========================================================

def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores: list[str] = []

    if inp.pdc_instalada_kw <= 0:
        errores.append("Pdc inválida.")

    if errores:
        return _resultado_error(inp, errores)

    # ------------------------------------------------------
    # SELECCIÓN DE MOTOR
    # ------------------------------------------------------

    modo = getattr(inp, "modo_simulacion", "mensual")
    if modo == "8760":

        resultado, errores = _modelo_8760(inp)

    else:

        resultado, errores = _modelo_hsp(inp)

    if errores:
        return _resultado_error(inp, errores)

    energia_bruta, energia_perdidas, energia_util, energia_recortada = resultado

    energia_bruta_anual = sum(energia_bruta)
    energia_util_anual = sum(energia_util)
    energia_curtailment_anual = sum(energia_recortada)

    pac = inp.pac_nominal_kw or 0

    dc_ac_ratio = inp.pdc_instalada_kw / pac if pac > 0 else 0.0

    return EnergiaResultado(
        ok=True,
        errores=[],
        pdc_instalada_kw=inp.pdc_instalada_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=dc_ac_ratio,
        energia_bruta_12m=energia_bruta,
        energia_despues_perdidas_12m=energia_perdidas,
        energia_curtailment_12m=energia_recortada,
        energia_util_12m=energia_util,
        energia_bruta_anual=energia_bruta_anual,
        energia_util_anual=energia_util_anual,
        energia_curtailment_anual=energia_curtailment_anual,
        meta={
            "motor": "8760" if inp.modo_simulacion == "8760" else "HSP",
            "meses": 12,
        },
    )
