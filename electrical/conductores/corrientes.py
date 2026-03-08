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
) -> ResultadoCorrientes:
    """
    Calcula corrientes eléctricas del sistema FV.

    Niveles eléctricos:

    Panel
        ↓
    String
        ↓
    MPPT
        ↓
    Inversor DC
        ↓
    Inversor AC
        ↓
    Sistema AC

    Entrega corrientes útiles para:
        - protecciones
        - conductores
        - reportes
    """

    cfg_tecnicos = cfg_tecnicos or {}

    # Factores de diseño NEC
    f_dc = float(cfg_tecnicos.get("factor_seguridad_dc", 1.25))
    f_ac = float(cfg_tecnicos.get("factor_seguridad_ac", 1.25))

    # ======================================================
    # Datos strings
    # ======================================================

    imp_string = _f(strings, "imp_string_a", 0.0)
    isc_string = _f(strings, "isc_string_a", 0.0)

    strings_por_mppt = _i(strings, "strings_por_mppt", 1)
    n_strings_total = _i(strings, "n_strings_total", 0)

    mppt_por_inv = _i(inv, "mppt", 1)

    # ======================================================
    # Corrientes DC
    # ======================================================

    # panel
    i_panel = imp_string

    # string
    i_string = imp_string

    # MPPT (strings en paralelo)
    i_mppt = imp_string * float(strings_por_mppt)

    # corriente total DC
    if n_strings_total > 0:
        isc_total = isc_string * float(n_strings_total)
    else:
        isc_total = isc_string

    # NEC DC
    i_dc_diseno = float(isc_total) * float(f_dc)

    # ======================================================
    # Corrientes AC
    # ======================================================

    i_ac_max_ds = _f(inv, "i_ac_max_a", 0.0)

    if i_ac_max_ds > 0.0:

        i_ac_max = i_ac_max_ds

    else:

        kw_ac = _f(inv, "kw_ac", 0.0)
        if kw_ac <= 0.0:
            kw_ac = _f(inv, "potencia_ac_kw", 0.0)

        p_w = kw_ac * 1000.0

        v = _f(inv, "v_ac_nom_v", 0.0)
        if v <= 0.0:
            v = _f(inv, "vac", 0.0)

        fases = _i(inv, "fases", 1)

        fp = _f(inv, "fp", 1.0)
        if fp <= 0:
            fp = 1.0

        if v <= 0 or p_w <= 0:

            i_ac_max = 0.0

        else:

            if fases == 3:
                i_ac_max = p_w / (math.sqrt(3) * v * fp)
            else:
                i_ac_max = p_w / (v * fp)

    i_ac_diseno = i_ac_max * f_ac

    # ======================================================
    # Shape estable
    # ======================================================

    return {

        # DC niveles
        "i_panel_a": float(i_panel),
        "i_string_a": float(i_string),
        "i_mppt_a": float(i_mppt),
        "i_dc_inversor_a": float(i_dc_diseno),

        # AC
        "i_ac_inversor_a": float(i_ac_max),
        "i_ac_diseno_a": float(i_ac_diseno),

        # Compatibilidad legacy
        "i_dc_diseno_a": float(i_dc_diseno),

        # Datos auxiliares
        "isc_total_a": float(isc_total),
        "f_dc": float(f_dc),
        "f_ac": float(f_ac),
    }
