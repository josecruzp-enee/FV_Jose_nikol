# electrical/corrientes.py
from __future__ import annotations

from electrical.modelos import ResultadoStrings, EntradaInversor, ResultadoCorrientes


def calcular_corrientes(strings: ResultadoStrings, inv: EntradaInversor, cfg_tecnicos: dict) -> ResultadoCorrientes:
    """
    Corrientes de diseño:
      - DC: Isc_total * factor_seguridad_dc
      - AC: usar i_ac_max datasheet si existe, si no estimar por P/V con factor
    """
    f_dc = float(cfg_tecnicos.get("factor_seguridad_dc", 1.25))
    f_ac = float(cfg_tecnicos.get("factor_seguridad_ac", 1.25))

    i_dc_diseno = strings.isc_string_a * f_dc

    if inv.i_ac_max_a is not None and inv.i_ac_max_a > 0:
        i_ac_max = inv.i_ac_max_a
    else:
        # estimación básica: I = P / V (monofásico) o P/(sqrt(3)*V) (3F)
        p_w = inv.potencia_ac_kw * 1000.0
        if inv.fases == 3:
            import math
            i_ac_max = p_w / (math.sqrt(3) * inv.v_ac_nom_v)
        else:
            i_ac_max = p_w / inv.v_ac_nom_v

    i_ac_diseno = i_ac_max * f_ac

    return ResultadoCorrientes(
        i_dc_diseno_a=float(i_dc_diseno),
        i_ac_diseno_a=float(i_ac_diseno),
        i_ac_max_a=float(i_ac_max),
    )
