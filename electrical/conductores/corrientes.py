"""
Subdominio corrientes — FV Engine (dentro de conductores por decisión de empaquetado).

Responsabilidad:
- Calcular corrientes de diseño DC/AC a partir de strings e inversor.
- Entregar un shape estable para protecciones/conductores.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Dict

ResultadoStrings = Mapping[str, Any]
EntradaInversor = Mapping[str, Any]
ResultadoCorrientes = Dict[str, float]


def _get(m: Mapping[str, Any] | None, k: str, default: Any = None) -> Any:
    if m is None:
        return default
    try:
        return m.get(k, default)
    except Exception:
        return default


def _f(m: Mapping[str, Any] | None, k: str, default: float = 0.0) -> float:
    try:
        v = _get(m, k, default)
        return float(v) if v is not None else float(default)
    except Exception:
        return float(default)


def _i(m: Mapping[str, Any] | None, k: str, default: int = 0) -> int:
    try:
        v = _get(m, k, default)
        return int(v) if v is not None else int(default)
    except Exception:
        return int(default)


def calcular_corrientes(
    strings: ResultadoStrings,
    inv: EntradaInversor,
    cfg_tecnicos: Mapping[str, Any] | None = None,
) -> ResultadoCorrientes:
    """
    Devuelve corrientes de diseño (DC/AC) para alimentar protecciones y conductores.

    DC:
      - Prioriza 'isc_array_a' si existe.
      - Si no, usa isc_string_a * n_strings_total si ambos existen.
      - Si no, cae a isc_string_a.

    AC:
      - Prioriza 'i_ac_max_a' (datasheet).
      - Si no, estima I = P / (V * fp) (1Φ) o I = P / (sqrt(3)*V*fp) (3Φ).
    """
    cfg_tecnicos = cfg_tecnicos or {}

    # Factores de diseño (defaults robustos)
    try:
        f_dc = float(cfg_tecnicos.get("factor_seguridad_dc", 1.25))
    except Exception:
        f_dc = 1.25

    try:
        f_ac = float(cfg_tecnicos.get("factor_seguridad_ac", 1.25))
    except Exception:
        f_ac = 1.25

    # --------------------
    # DC
    # --------------------
    isc_array = _f(strings, "isc_array_a", 0.0)
    n_strings_total = _i(strings, "n_strings_total", 0)
    isc_string = _f(strings, "isc_string_a", 0.0)

    if isc_array > 0.0:
        isc_total = isc_array
    elif n_strings_total > 0 and isc_string > 0.0:
        isc_total = isc_string * float(n_strings_total)
    else:
        isc_total = isc_string

    i_dc_diseno = float(isc_total) * float(f_dc)

    # --------------------
    # AC
    # --------------------
    i_ac_max_ds = _f(inv, "i_ac_max_a", 0.0)

    if i_ac_max_ds > 0.0:
        i_ac_max = i_ac_max_ds
    else:
        # Compat: acepta potencia en kw_ac o potencia_ac_kw
        kw_ac = _f(inv, "kw_ac", 0.0)
        if kw_ac <= 0.0:
            kw_ac = _f(inv, "potencia_ac_kw", 0.0)
        p_w = float(kw_ac) * 1000.0

        # Compat: acepta v_ac_nom_v o vac
        v = _f(inv, "v_ac_nom_v", 0.0)
        if v <= 0.0:
            v = _f(inv, "vac", 0.0)

        fases = _i(inv, "fases", 1)

        # Factor de potencia (si no viene, asumir 1.0)
        fp = _f(inv, "fp", 1.0)
        if fp <= 0.0:
            fp = 1.0

        if v <= 0.0 or p_w <= 0.0:
            i_ac_max = 0.0
        else:
            denom = (math.sqrt(3.0) * v * fp) if fases == 3 else (v * fp)
            i_ac_max = (p_w / denom) if denom > 0.0 else 0.0

    i_ac_diseno = float(i_ac_max) * float(f_ac)

    # Shape estable (keys fijas) para protecciones/conductores
    return {
        "i_dc_diseno_a": float(i_dc_diseno),
        "i_ac_diseno_a": float(i_ac_diseno),
        "i_ac_max_a": float(i_ac_max),
        "isc_total_a": float(isc_total),
        "f_dc": float(f_dc),
        "f_ac": float(f_ac),
    }
