"""
Subdominio corrientes — FV Engine

Responsabilidad:
- Calcular corrientes eléctricas del sistema FV.
- Separar niveles eléctricos reales:
    panel → string → MPPT → inversor → sistema AC
- Entregar un shape estable para protecciones/conductores.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Dict


ResultadoStrings = Mapping[str, Any]
EntradaInversor = Mapping[str, Any]
ResultadoCorrientes = Dict[str, float]


# ==========================================================
# Utilidades seguras
# ==========================================================

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


# ==========================================================
# Motor principal
# ==========================================================

def calcular_corrientes(
    strings: ResultadoStrings,
    inv: EntradaInversor,
    cfg_tecnicos: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:

    cfg_tecnicos = cfg_tecnicos or {}

    # Adaptador: si llega el resultado completo de paneles
    if isinstance(strings, dict) and "strings" in strings:
        if strings["strings"]:
            strings = strings["strings"][0]

    f_dc = float(cfg_tecnicos.get("factor_seguridad_dc", 1.25))
    f_ac = float(cfg_tecnicos.get("factor_seguridad_ac", 1.25))

    # ================================
    # Datos strings
    # ================================

    imp_string = _f(strings, "imp_string_a", 0.0)
    isc_string = _f(strings, "isc_string_a", 0.0)

    strings_por_mppt = _i(strings, "strings_por_mppt", 1)
    n_strings_total = _i(strings, "n_strings_total", 0)

    mppt_por_inv = _i(inv, "mppt", 1)

    # ================================
    # Panel
    # ================================

    i_panel = strings.get("panel_i", isc_string)

    # ================================
    # String
    # ================================

    i_string_operacion = imp_string
    isc_string_val = isc_string

    # ================================
    # MPPT
    # ================================

    i_mppt_operacion = imp_string * strings_por_mppt
    isc_mppt = isc_string * strings_por_mppt

    # NEC 690.8
    i_mppt_diseno = isc_mppt * f_dc

    # ================================
    # Sistema DC total
    # ================================

    i_dc_total_operacion = imp_string * n_strings_total
    isc_total = isc_string * n_strings_total

    # ================================
    # AC
    # ================================

    i_ac_max_ds = _f(inv, "i_ac_max_a", 0.0)

    if i_ac_max_ds > 0:
        i_ac = i_ac_max_ds

    else:

        kw_ac = _f(inv, "kw_ac", 0.0)
        if kw_ac <= 0:
            kw_ac = _f(inv, "potencia_ac_kw", 0.0)

        p_w = kw_ac * 1000.0

        v = _f(inv, "v_ac_nom_v", 0.0)
        if v <= 0:
            v = _f(inv, "vac", 0.0)

        fases = _i(inv, "fases", 1)

        fp = _f(inv, "fp", 1.0)
        if fp <= 0:
            fp = 1.0

        if v <= 0 or p_w <= 0:

            i_ac = 0.0

        else:

            if fases == 3:
                i_ac = p_w / (math.sqrt(3) * v * fp)
            else:
                i_ac = p_w / (v * fp)

    i_ac_diseno = i_ac * f_ac

    # ================================
    # Shape estable
    # ================================

    return {

        "panel": {
            "i_operacion_a": float(i_panel),
        },

        "string": {
            "i_operacion_a": float(i_string_operacion),
            "isc_a": float(isc_string_val),
        },

        "mppt": {
            "strings_paralelo": int(strings_por_mppt),
            "i_operacion_a": float(i_mppt_operacion),
            "isc_a": float(isc_mppt),
            "i_diseno_nec_a": float(i_mppt_diseno),
        },

        "dc_total": {
            "strings_total": int(n_strings_total),
            "i_operacion_a": float(i_dc_total_operacion),
            "isc_total_a": float(isc_total),
        },

        "ac": {
            "i_operacion_a": float(i_ac),
            "i_diseno_a": float(i_ac_diseno),
        },

        "factores": {
            "factor_dc": float(f_dc),
            "factor_ac": float(f_ac),
        }
    }
