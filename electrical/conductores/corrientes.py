"""
Subdominio corrientes — FV Engine (dentro de conductores por decisión de empaquetado).

Responsabilidad:
- Calcular corrientes de diseño DC/AC a partir de strings e inversor.
- Entregar un shape estable para protecciones/conductores.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

ResultadoStrings = Mapping[str, Any]
EntradaInversor = Mapping[str, Any]
ResultadoCorrientes = Mapping[str, Any]


def _f(m: Mapping[str, Any], k: str, default: float = 0.0) -> float:
    try:
        v = m.get(k, default)
        return float(v) if v is not None else float(default)
    except Exception:
        return float(default)


def _i(m: Mapping[str, Any], k: str, default: int = 0) -> int:
    try:
        v = m.get(k, default)
        return int(v) if v is not None else int(default)
    except Exception:
        return int(default)


def calcular_corrientes(strings: ResultadoStrings, inv: EntradaInversor, cfg_tecnicos: Mapping[str, Any]) -> ResultadoCorrientes:
    f_dc = float(cfg_tecnicos.get("factor_seguridad_dc", 1.25))
    f_ac = float(cfg_tecnicos.get("factor_seguridad_ac", 1.25))

    # DC: prioriza Isc del arreglo total si existe; si no, aproxima con Isc_string * n_strings_total.
    isc_array = _f(strings, "isc_array_a", 0.0)
    n_strings_total = _i(strings, "n_strings_total", 0)
    isc_string = _f(strings, "isc_string_a", 0.0)

    if isc_array > 0:
        isc_total = isc_array
    elif n_strings_total > 0 and isc_string > 0:
        isc_total = isc_string * n_strings_total
    else:
        isc_total = isc_string

    i_dc_diseno = isc_total * f_dc

    # AC: usa i_ac_max de datasheet si existe; si no, estima por potencia y tensión nominal.
    i_ac_max_ds = _f(inv, "i_ac_max_a", 0.0)
    if i_ac_max_ds > 0:
        i_ac_max = i_ac_max_ds
    else:
        p_w = _f(inv, "potencia_ac_kw", 0.0) * 1000.0
        v = _f(inv, "v_ac_nom_v", 0.0)
        fases = _i(inv, "fases", 1)

        if v <= 0 or p_w <= 0:
            i_ac_max = 0.0
        else:
            i_ac_max = p_w / (math.sqrt(3) * v) if fases == 3 else (p_w / v)

    i_ac_diseno = i_ac_max * f_ac

    # Shape estable (keys fijas) para protecciones/conductores
    return {
        "i_dc_diseno_a": float(i_dc_diseno),
        "i_ac_diseno_a": float(i_ac_diseno),
        "i_ac_max_a": float(i_ac_max),
        "isc_total_a": float(isc_total),
        "f_dc": float(f_dc),
        "f_ac": float(f_ac),
    }
