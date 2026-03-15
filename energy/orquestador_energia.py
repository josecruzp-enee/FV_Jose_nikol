from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO ENERGÍA — FV Engine
==========================================

Coordina el cálculo energético del sistema fotovoltaico.

Pipeline energético (modelo HSP):

    orientación del sistema
            ↓
    generación DC bruta
            ↓
    pérdidas DC + sombras
            ↓
    modelo energético del inversor
            ↓
    pérdidas AC
            ↓
    energía AC útil

Pipeline energético (modelo 8760):

    simulación horaria completa
            ↓
    agregación mensual
            ↓
    energía AC útil
"""

from .sistema.orientacion import factor_orientacion_total
from .sistema.generacion_bruta import calcular_energia_bruta_dc
from .sistema.perdidas_fisicas import aplicar_perdidas
from .sistema.perdidas_ac import aplicar_perdidas_ac
from .sistema.modelo_energetico_inversor import calcular_energia_inversor


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
        perdidas_ac_pct=0.0,  # AC se aplica después
        sombras_pct=inp.sombras_pct,
    )

    if not r_perdidas.ok:
        return None, r_perdidas.errores

    energia_despues_perdidas_dc = r_perdidas.energia_neta_12m_kwh

    # pérdidas DC
    energia_perdidas = [
        b - d for b, d in zip(energia_bruta, energia_despues_perdidas_dc)
    ]

    # ------------------------------------------------------
    # INVERSOR
    # ------------------------------------------------------

    r_inv = calcular_energia_inversor(
        energia_dc_12m=energia_despues_perdidas_dc,
        pdc_kw=inp.pdc_instalada_kw,
        pac_kw=inp.pac_nominal_kw,
        eficiencia_inv=inp.eficiencia_inversor,
        permitir_clipping=inp.permitir_clipping,
    )

    if not r_inv.ok:
        return None, r_inv.errores

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

    energia_util = r_ac.energia_ac_neta_12m_kwh

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
# MODELO 8760
# ==========================================================

def _modelo_8760(inp: EnergiaInput):

    sim = simular_8760(inp)

    if not sim.ok:
        return None, sim.errores

    energia_horas = sim.potencia_ac_horaria_kw

    energia_util = agregar_energia_por_mes(energia_horas)

    energia_bruta = energia_util
    energia_despues_perdidas = energia_util
    energia_perdidas = [0.0] * 12
    energia_clipping = [0.0] * 12

    return (
        energia_bruta,
        energia_perdidas,
        energia_despues_perdidas,
        energia_util,
        energia_clipping,
        None,
    ), []


# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores: list[str] = []

    if inp.pdc_instalada_kw <= 0:
        errores.append("Potencia DC inválida")

    if inp.pac_nominal_kw <= 0:
        errores.append("Potencia AC inválida")

    if errores:
        return _resultado_error(inp, errores)

    # ------------------------------------------------------
    # SELECCIÓN MOTOR
    # ------------------------------------------------------

    modo = getattr(inp, "modo_simulacion", "HSP")

    if modo == "8760":
        resultado, errores = _modelo_8760(inp)
    else:
        resultado, errores = _modelo_hsp(inp)

    if errores:
        return _resultado_error(inp, errores)

    (
        energia_bruta,
        energia_perdidas,
        energia_despues_perdidas,
        energia_util,
        energia_clipping,
        factor_orientacion,
    ) = resultado

    # ------------------------------------------------------
    # AGREGACIÓN ANUAL
    # ------------------------------------------------------

    energia_bruta_anual = sum(energia_bruta)
    energia_perdidas_anual = sum(energia_perdidas)
    energia_despues_perdidas_anual = sum(energia_despues_perdidas)
    energia_util_anual = sum(energia_util)
    energia_clipping_anual = sum(energia_clipping)

    pac = inp.pac_nominal_kw

    dc_ac_ratio = inp.pdc_instalada_kw / pac if pac > 0 else 0.0

    return EnergiaResultado(

        ok=True,
        errores=[],

        pdc_instalada_kw=inp.pdc_instalada_kw,
        pac_nominal_kw=inp.pac_nominal_kw,

        dc_ac_ratio=dc_ac_ratio,

        energia_bruta_12m=energia_bruta,
        energia_perdidas_12m=energia_perdidas,
        energia_despues_perdidas_12m=energia_despues_perdidas,
        energia_clipping_12m=energia_clipping,
        energia_util_12m=energia_util,

        energia_bruta_anual=energia_bruta_anual,
        energia_perdidas_anual=energia_perdidas_anual,
        energia_despues_perdidas_anual=energia_despues_perdidas_anual,
        energia_clipping_anual=energia_clipping_anual,
        energia_util_anual=energia_util_anual,

        meta={
            "motor": modo,
            "meses": 12,
            "factor_orientacion": factor_orientacion,
        },
    )
