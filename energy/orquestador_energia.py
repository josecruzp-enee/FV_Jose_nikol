from __future__ import annotations

from dataclasses import dataclass
from typing import List

from energy.contrato import EnergiaResultado, EnergiaInput
from energy.sistema.agregacion_8760 import agregar_energia_por_mes

import streamlit as st


# ==========================================================
# RESULTADO ERROR
# ==========================================================
def _resultado_error(inp, errores):

    paneles = inp.paneles

    pdc_kw = 0.0
    if paneles and hasattr(paneles, "array"):
        pdc_kw = paneles.array.pdc_kw

    return EnergiaResultado(
        ok=False,
        errores=errores,

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=0.0,

        energia_horaria_kwh=[],

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

        produccion_especifica_kwh_kwp=0.0,
        performance_ratio=0.0,

        meta={}
    )


# ==========================================================
# CLIMA
# ==========================================================
def _simular_estado_8760(inp: EnergiaInput):

    from energy.clima.simulacion_8760 import simular_clima_8760

    resultado = simular_clima_8760(
        clima=inp.clima,
        tilt=inp.tilt_deg,
        azimuth=inp.azimut_deg,
    )

    return resultado.horas


# ==========================================================
# DC
# ==========================================================
def _calcular_dc(inp, estado):

    paneles = inp.paneles

    if paneles is None:
        raise ValueError("paneles es None")

    if not getattr(paneles, "ok", False):
        raise ValueError(f"paneles inválido: {paneles.errores}")

    if not hasattr(paneles, "array"):
        raise ValueError("paneles sin atributo array")

    pdc_kw = paneles.array.pdc_kw
    poa = estado.poa_wm2

    if poa is None:
        raise ValueError("estado sin poa_wm2")

    factor = max(poa / 1000.0, 0.0)

    return pdc_kw * factor


# ==========================================================
# PÉRDIDAS DC (CORREGIDO)
# ==========================================================
def _aplicar_perdidas_dc(inp: EnergiaInput, potencia_dc_kw):

    from energy.sistema.perdidas_fisicas import (
        aplicar_perdidas_fisicas, PerdidasInput
    )

    @dataclass(frozen=True)
    class ResultadoDC:
        potencia_bruta_kw: List[float]
        potencia_neta_kw: List[float]
        perdidas_kw: List[float]
        factor_total: float

    base = aplicar_perdidas_fisicas(
        PerdidasInput(
            potencia_kw=potencia_dc_kw,
            perdidas_dc_pct=inp.perdidas_dc_pct,
            sombras_pct=inp.sombras_pct,
        )
    )

    potencia_neta = base.potencia_kw

    perdidas = [
        p_in - p_out
        for p_in, p_out in zip(potencia_dc_kw, potencia_neta)
    ]

    return ResultadoDC(
        potencia_bruta_kw=potencia_dc_kw,
        potencia_neta_kw=potencia_neta,
        perdidas_kw=perdidas,
        factor_total=base.factor_total,
    )


# ==========================================================
# INVERSOR
# ==========================================================
def _aplicar_inversor(inp: EnergiaInput, potencia_dc_kw):

    from energy.sistema.modelo_energetico_inversor import (
        calcular_inversor_8760, Inversor8760Input
    )

    return calcular_inversor_8760(
        Inversor8760Input(
            potencia_dc_kw=potencia_dc_kw,
            p_ac_nominal_kw=inp.pac_nominal_kw,
            eficiencia_nominal=inp.eficiencia_inversor,
        )
    )


# ==========================================================
# PÉRDIDAS AC
# ==========================================================
# ==========================================================
# PÉRDIDAS AC (CORREGIDO - TRAZABLE)
# ==========================================================
def _aplicar_perdidas_ac(inp: EnergiaInput, potencia_ac_kw):

    from energy.sistema.perdidas_ac import (
        aplicar_perdidas_ac, PerdidasACInput
    )
    from dataclasses import dataclass
    from typing import List

    # ------------------------------------------------------
    # CONTRATO CORRECTO
    # ------------------------------------------------------
    @dataclass(frozen=True)
    class ResultadoAC:
        potencia_bruta_kw: List[float]
        potencia_neta_kw: List[float]
        perdidas_kw: List[float]

    base = aplicar_perdidas_ac(
        PerdidasACInput(
            potencia_kw=potencia_ac_kw,
            perdidas_ac_pct=inp.perdidas_ac_pct,
        )
    )

    potencia_neta = base.potencia_kw

    perdidas = [
        p_in - p_out
        for p_in, p_out in zip(potencia_ac_kw, potencia_neta)
    ]

    return ResultadoAC(
        potencia_bruta_kw=potencia_ac_kw,
        potencia_neta_kw=potencia_neta,
        perdidas_kw=perdidas,
    )

# ==========================================================
# RESULTADO (CORREGIDO)
# ==========================================================
def _construir_resultado(
    inp,
    dc_bruta_kw,
    dc_neta_kw,
    perdidas_dc_kw,
    ac_bruta_kw,
    clipping_kw,
    ac_neta_kw,
    perdidas_ac_kw,
    energia_horaria_kwh,
):

    energia_bruta_12m = agregar_energia_por_mes(dc_bruta_kw)
    energia_final_12m = agregar_energia_por_mes(ac_neta_kw)
    energia_clipping_12m = agregar_energia_por_mes(clipping_kw)

    energia_bruta_anual = sum(dc_bruta_kw)
    energia_final_anual = sum(ac_neta_kw)
    energia_clipping_anual = sum(clipping_kw)

    pdc_kw = inp.paneles.array.pdc_kw

    produccion_especifica_kwh_kwp = (
        energia_final_anual / pdc_kw if pdc_kw > 0 else 0.0
    )

    performance_ratio = (
        energia_final_anual / energia_bruta_anual
        if energia_bruta_anual > 0 else 0.0
    )

    return EnergiaResultado(
        ok=True,
        errores=[],

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=pdc_kw / inp.pac_nominal_kw if inp.pac_nominal_kw else 0.0,

        energia_horaria_kwh=energia_horaria_kwh,

        energia_bruta_12m=energia_bruta_12m,
        energia_perdidas_12m=[b - f for b, f in zip(energia_bruta_12m, energia_final_12m)],
        energia_despues_perdidas_12m=energia_final_12m,
        energia_clipping_12m=energia_clipping_12m,
        energia_util_12m=energia_final_12m,

        energia_bruta_anual=energia_bruta_anual,
        energia_perdidas_anual=energia_bruta_anual - energia_final_anual,
        energia_despues_perdidas_anual=energia_final_anual,
        energia_clipping_anual=energia_clipping_anual,
        energia_util_anual=energia_final_anual,

        produccion_especifica_kwh_kwp=produccion_especifica_kwh_kwp,
        performance_ratio=performance_ratio,

        meta={"motor": "8760"},
    )


# ==========================================================
# MAIN
# ==========================================================
def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = inp.validar()
    if errores:
        return _resultado_error(inp, errores)

    estados = _simular_estado_8760(inp)

    potencia_dc_bruta = [
        _calcular_dc(inp, estado)
        for estado in estados
    ]

    r_dc = _aplicar_perdidas_dc(inp, potencia_dc_bruta)

    inv = _aplicar_inversor(inp, r_dc.potencia_neta_kw)

    r_ac = _aplicar_perdidas_ac(inp, inv.potencia_ac_kw)

    energia_horaria_kwh = r_ac.potencia_neta_kw

    return _construir_resultado(
        inp=inp,
        dc_bruta_kw=potencia_dc_bruta,
        dc_neta_kw=r_dc.potencia_neta_kw,
        perdidas_dc_kw=r_dc.perdidas_kw,
        ac_bruta_kw=inv.potencia_ac_kw,
        clipping_kw=inv.clipping_kw,
        ac_neta_kw=r_ac.potencia_neta_kw,
        perdidas_ac_kw=r_ac.perdidas_kw,
        energia_horaria_kwh=energia_horaria_kwh,
    )
