from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO ENERGÍA — FV Engine
===========================================

Este módulo coordina el cálculo energético del sistema FV.

Responsabilidad
---------------

Ejecutar el motor energético seleccionando entre:

• Modelo HSP mensual (rápido)
• Simulación 8760 (detallada)

Pipeline del modelo HSP
-----------------------

    generación DC bruta
            ↓
    pérdidas físicas
            ↓
    limitación del inversor (curtailment)
            ↓
    energía útil

Pipeline del modelo 8760
------------------------

    simulación horaria del sistema
            ↓
    agregación mensual
            ↓
    energía útil

Salida del dominio
------------------

Este módulo produce un único objeto:

    EnergiaResultado
"""

from .contrato import EnergiaInput, EnergiaResultado

from .generacion_bruta import calcular_energia_bruta_dc
from .perdidas_fisicas import aplicar_perdidas
from .limitacion_inversor import aplicar_curtailment

# motor avanzado
from .clima.simulacion_8760 import simular_8760
from .clima.agregacion_8760 import agregar_energia_por_mes


# ==========================================================
# RESULTADO DE ERROR
# ==========================================================

def _resultado_error(inp: EnergiaInput, errores: list[str]) -> EnergiaResultado:
    """
    Construye un resultado consistente cuando ocurre un error.
    """

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
# MODELO HSP (MENSUAL)
# ==========================================================

def _modelo_hsp(inp: EnergiaInput):
    """
    Ejecuta el modelo energético mensual basado en HSP.
    """

    # ------------------------------------------------------
    # Generación DC bruta
    # ------------------------------------------------------

    r_bruta = calcular_energia_bruta_dc(
        pdc_kw=inp.pdc_instalada_kw,
        hsp_12m=inp.hsp_12m,
        dias_mes=inp.dias_mes,
        factor_orientacion=inp.factor_orientacion,
    )

    if not r_bruta.ok:
        return None, r_bruta.errores

    energia_bruta = r_bruta.energia_mensual_dc_kwh

    # ------------------------------------------------------
    # Aplicar pérdidas físicas
    # ------------------------------------------------------

    r_perdidas = aplicar_perdidas(
        energia_dc_12m=energia_bruta,
        perdidas_dc_pct=inp.perdidas_dc_pct,
        perdidas_ac_pct=inp.perdidas_ac_pct,
        sombras_pct=inp.sombras_pct,
    )

    if not r_perdidas.ok:
        return None, r_perdidas.errores

    energia_perdidas = r_perdidas.energia_neta_12m_kwh

    # ------------------------------------------------------
    # Limitación del inversor
    # ------------------------------------------------------

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
    """
    Ejecuta la simulación energética horaria (8760).
    """

    sim = simular_8760(inp)

    if not sim.ok:
        return None, sim.errores

    energia_horas = sim.potencia_ac_horaria_kw

    energia_mensual = agregar_energia_por_mes(energia_horas)

    # En simulación 8760 la energía ya incluye pérdidas
    return (
        energia_mensual,
        energia_mensual,
        energia_mensual,
        [0.0] * 12,
    ), []


# ==========================================================
# MOTOR ENERGÉTICO PRINCIPAL
# ==========================================================

def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:
    """
    Ejecuta el cálculo energético completo del sistema FV.
    """

    errores: list[str] = []

    # ------------------------------------------------------
    # Validación básica
    # ------------------------------------------------------

    if inp.pdc_instalada_kw <= 0:
        errores.append("Pdc inválida.")

    if errores:
        return _resultado_error(inp, errores)

    # ------------------------------------------------------
    # Selección del motor de simulación
    # ------------------------------------------------------

    modo = getattr(inp, "modo_simulacion", "mensual")

    if modo == "8760":

        resultado, errores = _modelo_8760(inp)

    else:

        resultado, errores = _modelo_hsp(inp)

    if errores:
        return _resultado_error(inp, errores)

    energia_bruta, energia_perdidas, energia_util, energia_recortada = resultado

    # ------------------------------------------------------
    # Agregación anual
    # ------------------------------------------------------

    energia_bruta_anual = sum(energia_bruta)
    energia_util_anual = sum(energia_util)
    energia_curtailment_anual = sum(energia_recortada)

    # ------------------------------------------------------
    # Cálculo del DC/AC ratio
    # ------------------------------------------------------

    pac = inp.pac_nominal_kw or 0
    dc_ac_ratio = inp.pdc_instalada_kw / pac if pac > 0 else 0.0

    # ------------------------------------------------------
    # Resultado final
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
        meta={
            "motor": "8760" if modo == "8760" else "HSP",
            "meses": 12,
        },
    )
