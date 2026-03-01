# electrical/energia/orquestador_energia.py
from __future__ import annotations

from typing import Dict, Any

from .contrato import EnergiaInput, EnergiaResultado
from .generacion_bruta import calcular_energia_bruta_dc
from .perdidas_fisicas import aplicar_perdidas
from .limitacion_inversor import aplicar_curtailment


def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = []

    if inp.pdc_instalada_kw <= 0:
        errores.append("Pdc inválida.")

    if len(inp.hsp_12m) != 12:
        errores.append("HSP debe tener 12 meses.")

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

    energia_bruta = calcular_energia_bruta_dc(
        pdc_kw=inp.pdc_instalada_kw,
        hsp_12m=inp.hsp_12m,
        dias_mes=inp.dias_mes,
        factor_orientacion=inp.factor_orientacion,
    )

    energia_perdidas = aplicar_perdidas(
        energia_dc_12m=energia_bruta,
        perdidas_dc_pct=inp.perdidas_dc_pct,
        perdidas_ac_pct=inp.perdidas_ac_pct,
        sombras_pct=inp.sombras_pct,
    )

    energia_util, energia_recortada = aplicar_curtailment(
        energia_12m=energia_perdidas,
        pdc_kw=inp.pdc_instalada_kw,
        pac_kw=inp.pac_nominal_kw,
        permitir=inp.permitir_curtailment,
    )

    return EnergiaResultado(
        ok=True,
        errores=[],
        pdc_instalada_kw=inp.pdc_instalada_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=inp.pdc_instalada_kw / inp.pac_nominal_kw
        if inp.pac_nominal_kw > 0 else 0.0,
        energia_bruta_12m=energia_bruta,
        energia_despues_perdidas_12m=energia_perdidas,
        energia_curtailment_12m=energia_recortada,
        energia_util_12m=energia_util,
        energia_bruta_anual=sum(energia_bruta),
        energia_util_anual=sum(energia_util),
        energia_curtailment_anual=sum(energia_recortada),
        meta={},
    )
