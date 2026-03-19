from __future__ import annotations


from dataclasses import dataclass, field
from typing import List, Dict, Any
from energy.sistema.agregacion_8760 import agregar_energia_por_mes

import streamlit as st


# ==========================================================
# HELPERS (PARCHE COMPATIBILIDAD)
# ==========================================================

def _get_pdc_kw(paneles):
    """
    Soporta:
        - dict (legacy)
        - ResultadoPaneles (nuevo)
    """

    # Caso dict (legacy)
    if isinstance(paneles, dict):
        return paneles.get("pdc_total_kw")

    # Caso objeto nuevo
    if hasattr(paneles, "array") and hasattr(paneles.array, "pdc_kw"):
        return paneles.array.pdc_kw

    return None


def _paneles_ok(paneles):

    if isinstance(paneles, dict):
        return paneles.get("ok", False)

    return getattr(paneles, "ok", False)


# ==========================================================
# RESULTADO ERROR
# ==========================================================

def _resultado_error(inp, errores):

    paneles = inp.paneles
    pdc_kw = _get_pdc_kw(paneles) or 0.0

    return EnergiaResultado(
        ok=False,
        errores=errores,

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,

        dc_ac_ratio=0.0,

        energia_horaria=[],

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

        meta={}
    )


# ==========================================================
# 1. CLIMA
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
# 2. DC
# ==========================================================

def _calcular_dc(inp, estado):

    paneles = inp.paneles

    # ------------------------------------------------------
    # VALIDACIÓN FLEXIBLE (PARCHE)
    # ------------------------------------------------------
    if paneles is None:
        raise ValueError("paneles es None")

    if not _paneles_ok(paneles):
        raise ValueError("paneles no válido")

    pdc_kw = _get_pdc_kw(paneles)

    if pdc_kw is None:
        raise ValueError(f"No se pudo obtener pdc_kw de paneles: {paneles}")

    # ------------------------------------------------------
    # DATOS BASE
    # ------------------------------------------------------
    poa = estado.poa_wm2

    if poa is None:
        raise ValueError("estado sin poa_wm2")

    # ------------------------------------------------------
    # MODELO
    # ------------------------------------------------------
    factor_irradiancia = max(poa / 1000.0, 0.0)

    pdc_w = pdc_kw * 1000.0 * factor_irradiancia

    return pdc_w


# ==========================================================
# 3. PÉRDIDAS DC
# ==========================================================

def _aplicar_perdidas_dc(inp: EnergiaInput, potencia_dc_kw):

    from energy.sistema.perdidas_fisicas import (
        aplicar_perdidas_fisicas, PerdidasInput
    )

    return aplicar_perdidas_fisicas(
        PerdidasInput(
            potencia_kw=potencia_dc_kw,
            perdidas_dc_pct=inp.perdidas_dc_pct,
            sombras_pct=inp.sombras_pct,
        )
    )


# ==========================================================
# 4. INVERSOR
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
# 5. PÉRDIDAS AC
# ==========================================================

def _aplicar_perdidas_ac(inp: EnergiaInput, potencia_ac_kw):

    from energy.sistema.perdidas_ac import (
        aplicar_perdidas_ac, PerdidasACInput
    )

    return aplicar_perdidas_ac(
        PerdidasACInput(
            potencia_kw=potencia_ac_kw,
            perdidas_ac_pct=inp.perdidas_ac_pct,
        )
    )


# ==========================================================
# 6. RESULTADO
# ==========================================================

def _construir_resultado(inp, potencia_dc_kw, potencia_ac_kw, clipping_kw):

    energia_bruta_12m = agregar_energia_por_mes(potencia_dc_kw)
    energia_final_12m = agregar_energia_por_mes(potencia_ac_kw)
    energia_clipping_12m = agregar_energia_por_mes(clipping_kw)

    energia_bruta_anual = sum(potencia_dc_kw)
    energia_final_anual = sum(potencia_ac_kw)
    energia_clipping_anual = sum(clipping_kw)

    pdc_kw = _get_pdc_kw(inp.paneles) or 0.0

    return EnergiaResultado(
        ok=True,
        errores=[],

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=pdc_kw / inp.pac_nominal_kw if inp.pac_nominal_kw else 0.0,

        energia_horaria=[],

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

        meta={"motor": "8760"},
    )


# ==========================================================
# MAIN
# ==========================================================

def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = inp.validar()

    # 🔥 PARCHE: ignorar error de dict (temporal)
    errores = [e for e in errores if e != "paneles debe ser dict"]

    if errores:
        return _resultado_error(inp, errores)

    estado = _simular_estado_8760(inp)

    potencia_dc = _calcular_dc(inp, estado)

    r_dc = _aplicar_perdidas_dc(inp, potencia_dc)

    inv = _aplicar_inversor(inp, r_dc.potencia_kw)

    r_ac = _aplicar_perdidas_ac(inp, inv.potencia_ac_kw)

    return _construir_resultado(
        inp,
        potencia_dc,
        r_ac.potencia_kw,
        inv.clipping_kw,
    )
