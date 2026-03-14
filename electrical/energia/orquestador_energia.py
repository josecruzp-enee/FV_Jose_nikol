from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO ENERGÍA — FV Engine
===========================================

Coordina el cálculo energético del sistema fotovoltaico.

Motores disponibles
-------------------

• Modelo HSP mensual (rápido)
• Simulación horaria 8760 (detallada)

Pipeline energético (HSP)
-------------------------

    generación DC bruta
            ↓
    pérdidas físicas
            ↓
    modelo energético del inversor
            ↓
    energía AC útil

Pipeline energético (8760)
--------------------------

    simulación horaria
            ↓
    agregación mensual
            ↓
    energía AC útil

Salida del dominio
------------------

EnergiaResultado
"""

from .contrato import EnergiaInput, EnergiaResultado

from .generacion_bruta import calcular_energia_bruta_dc
from .perdidas_fisicas import aplicar_perdidas
from .modelo_inversor import aplicar_modelo_inversor

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
    # Modelo energético del inversor
    # ------------------------------------------------------

    r_inv = aplicar_modelo_inversor(
        energia_dc_12m=energia_perdidas,
        pdc_kw=inp.pdc_instalada_kw,
        pac_kw=inp.pac_nominal_kw,
        eficiencia_inv=inp.eficiencia_inversor,
        permitir_curtailment=inp.permitir_curtailment,
    )

    if not r_inv.ok:
        return None, r_inv.errores

    energia_ac = r_inv.energia_ac_12m_kwh
    energia_curtailment = r_inv.energia_curtailment_12m_kwh

    return (
        energia_bruta,
        energia_perdidas,
        energia_ac,
        energia_curtailment,
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

    # En el modelo 8760 ya se incluye pérdidas e inversor
    energia_util = energia_mensual

    return (
        energia_util,      # bruta (placeholder)
        energia_util,      # después pérdidas
        energia_util,      # energía útil
        [0.0] * 12,        # curtailment estimado
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

    if inp.pac_nominal_kw <= 0:
        errores.append("Pac inválida.")

    if errores:
        return _resultado_error(inp, errores)

    # ------------------------------------------------------
    # Selección del motor
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
    # DC / AC ratio
    # ------------------------------------------------------

    pac = inp.pac_nominal_kw
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

