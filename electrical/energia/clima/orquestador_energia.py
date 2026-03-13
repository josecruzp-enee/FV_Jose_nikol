from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO ENERGIA

Este módulo coordina el cálculo energético completo del sistema FV.

FRONTERA DEL DOMINIO
--------------------

Entrada:
    EnergiaInput

Salida:
    EnergiaResultado

Flujo interno:

    generacion_bruta
            ↓
    perdidas_fisicas
            ↓
    limitacion_inversor

Este archivo es la única interfaz pública del dominio energía.
Core debe interactuar únicamente con este módulo.
"""

from .contrato import EnergiaInput, EnergiaResultado

from .generacion_bruta import calcular_energia_bruta_dc
from .perdidas_fisicas import aplicar_perdidas
from .limitacion_inversor import aplicar_curtailment


# ==========================================================
# MOTOR ENERGÉTICO
# ==========================================================

def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = []

    # ------------------------------------------------------
    # Validaciones básicas de entrada
    # ------------------------------------------------------

    if inp.pdc_instalada_kw <= 0:
        errores.append("Pdc inválida.")

    if len(inp.hsp_12m) != 12:
        errores.append("HSP debe tener 12 meses.")

    if len(inp.dias_mes) != 12:
        errores.append("dias_mes debe tener 12 valores.")

    if errores:

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
            meta={},
        )

    # ------------------------------------------------------
    # 1. Generación DC bruta
    # ------------------------------------------------------

    r_bruta = calcular_energia_bruta_dc(
        pdc_kw=inp.pdc_instalada_kw,
        hsp_12m=inp.hsp_12m,
        dias_mes=inp.dias_mes,
        factor_orientacion=inp.factor_orientacion,
    )

    if not r_bruta.ok:

        return EnergiaResultado(
            ok=False,
            errores=r_bruta.errores,
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
            meta={},
        )

    energia_bruta = r_bruta.energia_mensual_dc_kwh

    # ------------------------------------------------------
    # 2. Aplicar pérdidas físicas
    # ------------------------------------------------------

    r_perdidas = aplicar_perdidas(
        energia_dc_12m=energia_bruta,
        perdidas_dc_pct=inp.perdidas_dc_pct,
        perdidas_ac_pct=inp.perdidas_ac_pct,
        sombras_pct=inp.sombras_pct,
    )

    if not r_perdidas.ok:

        return EnergiaResultado(
            ok=False,
            errores=r_perdidas.errores,
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
            meta={},
        )

    energia_perdidas = r_perdidas.energia_neta_12m_kwh

    # ------------------------------------------------------
    # 3. Curtailment por inversor
    # ------------------------------------------------------

    r_curt = aplicar_curtailment(
        energia_12m=energia_perdidas,
        pdc_kw=inp.pdc_instalada_kw,
        kw_ac=inp.pac_nominal_kw,
        permitir=inp.permitir_curtailment,
    )

    if not r_curt.ok:

        return EnergiaResultado(
            ok=False,
            errores=r_curt.errores,
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
            meta={},
        )

    energia_util = r_curt.energia_final_12m_kwh
    energia_recortada = r_curt.energia_recortada_12m_kwh

    # ------------------------------------------------------
    # Cálculos finales
    # ------------------------------------------------------

    energia_bruta_anual = sum(energia_bruta)
    energia_util_anual = sum(energia_util)
    energia_curtailment_anual = sum(energia_recortada)

    dc_ac_ratio = (
        inp.pdc_instalada_kw / inp.pac_nominal_kw
        if inp.pac_nominal_kw > 0
        else 0.0
    )

    # ------------------------------------------------------
    # Resultado final del dominio
    # ------------------------------------------------------

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
        meta={},
    )


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# ejecutar_motor_energia()
#
# Entrada:
# EnergiaInput
#
# Salida:
# EnergiaResultado
#
# Descripción:
# Ejecuta el modelo energético completo del sistema FV
# aplicando generación, pérdidas y limitación del inversor.
#
# Consumido por:
# core.orquestador_estudio
#
# ==========================================================
