"""
Subdominio corrientes — FV Engine

Responsabilidad:
- Calcular corrientes eléctricas del sistema FV.
- Separar niveles eléctricos reales:

    panel → string → MPPT → inversor → sistema AC

Salida estable para:
- protecciones
- conductores
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from .resultado_corriente import ResultadoCorrientes, NivelCorriente


ResultadoStrings = Mapping[str, Any]
EntradaInversor = Mapping[str, Any]


# ==========================================================
# UTILIDADES SEGURAS
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
# MOTOR PRINCIPAL
# ==========================================================

def calcular_corrientes(
    strings: ResultadoStrings,
    inv: EntradaInversor,
    cfg_tecnicos: Mapping[str, Any] | None = None,
) -> ResultadoCorrientes:

    cfg_tecnicos = cfg_tecnicos or {}

    f_dc = float(cfg_tecnicos.get("factor_seguridad_dc", 1.25))
    f_ac = float(cfg_tecnicos.get("factor_seguridad_ac", 1.25))

    # ======================================================
    # Adaptador entrada resultado strings
    # ======================================================

    if isinstance(strings, dict) and "strings" in strings:

        lista = strings.get("strings", [])
        rec = strings.get("recomendacion", {})

        if not lista:
            raise ValueError("Resultado strings vacío")

        s0 = lista[0]

        strings_por_mppt = _i(s0, "n_paralelo", 1)
        n_strings_total = _i(rec, "n_strings_total", 0)

        imp_string = _f(s0, "imp_string_a", 0.0)
        isc_string = _f(s0, "isc_string_a", 0.0)

        i_panel = isc_string

    else:

        imp_string = _f(strings, "imp_string_a", 0.0)
        isc_string = _f(strings, "isc_string_a", 0.0)

        strings_por_mppt = _i(strings, "strings_por_mppt", 1)
        n_strings_total = _i(strings, "n_strings_total", 0)

        i_panel = _f(strings, "panel_i", isc_string)

    if n_strings_total <= 0:
        raise ValueError("n_strings_total inválido para cálculo de corrientes")

    # ======================================================
    # STRING
    # ======================================================

    i_string_operacion = imp_string
    i_string_diseno = isc_string * f_dc

    # ======================================================
    # MPPT
    # ======================================================

    i_mppt_operacion = imp_string * strings_por_mppt
    isc_mppt = isc_string * strings_por_mppt

    i_mppt_diseno = isc_mppt * f_dc

    # ======================================================
    # DC TOTAL
    # ======================================================

    i_dc_total_operacion = imp_string * n_strings_total
    isc_total = isc_string * n_strings_total

    # NEC 690.8
    i_dc_diseno = isc_total * f_dc

    # ======================================================
    # AC
    # ======================================================

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

    # ======================================================
    # RESULTADO TIPADO
    # ======================================================

    return ResultadoCorrientes(

        panel=NivelCorriente(
            i_operacion_a=float(i_panel),
            i_diseno_a=float(i_panel * f_dc),
        ),

        string=NivelCorriente(
            i_operacion_a=float(i_string_operacion),
            i_diseno_a=float(i_string_diseno),
        ),

        mppt=NivelCorriente(
            i_operacion_a=float(i_mppt_operacion),
            i_diseno_a=float(i_mppt_diseno),
        ),

        dc_total=NivelCorriente(
            i_operacion_a=float(i_dc_total_operacion),
            i_diseno_a=float(i_dc_diseno),
        ),

        ac=NivelCorriente(
            i_operacion_a=float(i_ac),
            i_diseno_a=float(i_ac_diseno),
        ),
    )
