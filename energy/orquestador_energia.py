from __future__ import annotations

from dataclasses import dataclass
from typing import List

from energy.contrato import EnergiaResultado, EnergiaInput
from energy.sistema.agregacion_8760 import agregar_energia_por_mes


# ==========================================================
# RESULTADO ERROR
# ==========================================================
def _resultado_error(inp: EnergiaInput, errores: List[str]) -> EnergiaResultado:

    paneles = inp.paneles

    pdc_kw: float = 0.0
    if paneles and hasattr(paneles, "array"):
        pdc_kw = paneles.array.potencia_dc_w / 1000

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
# NORMALIZACIÓN PANEL (🔥 CLAVE)
# ==========================================================
def _normalizar_panel(panel):

    return {
        "p_nom": getattr(panel, "pmax_w", 0.0),
        "vmp": getattr(panel, "vmp_v", 0.0),
        "voc": getattr(panel, "voc_v", 0.0),
        "imp": getattr(panel, "imp_a", 0.0),
        "isc": getattr(panel, "isc_a", 0.0),

        "coef_vmp": getattr(panel, "coef_vmp_pct_c", -0.3) / 100,
        "coef_voc": getattr(panel, "coef_voc_pct_c", -0.3) / 100,
        "coef_p": getattr(panel, "coef_potencia_pct_c", -0.35) / 100,

        "noct": getattr(panel, "noct_c", 45.0),
    }


# ==========================================================
# DC (ACTUAL - SIMPLE PERO CORRECTO)
# ==========================================================
def _calcular_dc(inp: EnergiaInput, estado) -> float:

    paneles = inp.paneles

    if paneles is None:
        raise ValueError("paneles es None")

    if not getattr(paneles, "ok", False):
        raise ValueError(f"paneles inválido: {paneles.errores}")

    if not hasattr(paneles, "array"):
        raise ValueError("paneles sin atributo array")

    pdc_kw: float = paneles.array.potencia_dc_w / 1000

    poa = getattr(estado, "poa_wm2", None)
    if poa is None:
        raise ValueError("estado sin poa_wm2")

    factor = max(poa / 1000.0, 0.0)

    return pdc_kw * factor


# ==========================================================
# PÉRDIDAS DC
# ==========================================================
def _aplicar_perdidas_dc(inp: EnergiaInput, potencia_dc_kw: List[float]):

    from energy.sistema.perdidas_fisicas import (
        aplicar_perdidas_fisicas, PerdidasInput
    )

    @dataclass(frozen=True)
    class ResultadoDC:
        potencia_bruta_kw: List[float]
        potencia_neta_kw: List[float]
        perdidas_kw: List[float]

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
    )


# ==========================================================
# INVERSOR
# ==========================================================
def _aplicar_inversor(inp: EnergiaInput, potencia_dc_kw: List[float]):

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
def _aplicar_perdidas_ac(inp: EnergiaInput, potencia_ac_kw: List[float]):

    from energy.sistema.perdidas_ac import (
        aplicar_perdidas_ac, PerdidasACInput
    )

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
# RESULTADO
# ==========================================================
def _construir_resultado(
    inp: EnergiaInput,
    dc_bruta_kw: List[float],
    ac_neta_kw: List[float],
    clipping_kw: List[float],
) -> EnergiaResultado:

    energia_bruta_12m = agregar_energia_por_mes(dc_bruta_kw)
    energia_final_12m = agregar_energia_por_mes(ac_neta_kw)
    energia_clipping_12m = agregar_energia_por_mes(clipping_kw)

    energia_bruta_anual = sum(dc_bruta_kw)
    energia_final_anual = sum(ac_neta_kw)
    energia_clipping_anual = sum(clipping_kw)

    pdc_kw = inp.paneles.array.potencia_dc_w / 1000

    return EnergiaResultado(
        ok=True,
        errores=[],

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=pdc_kw / inp.pac_nominal_kw if inp.pac_nominal_kw else 0.0,

        energia_horaria_kwh=[p for p in ac_neta_kw],

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

        produccion_especifica_kwh_kwp=(
            energia_final_anual / pdc_kw if pdc_kw > 0 else 0.0
        ),

        performance_ratio=(
            energia_final_anual / energia_bruta_anual
            if energia_bruta_anual > 0 else 0.0
        ),

        meta={"motor": "8760_estable"},
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

    return _construir_resultado(
        inp=inp,
        dc_bruta_kw=potencia_dc_bruta,
        ac_neta_kw=r_ac.potencia_neta_kw,
        clipping_kw=inv.clipping_kw,
    )
