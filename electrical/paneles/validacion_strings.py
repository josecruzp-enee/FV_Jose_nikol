from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .orquestador_paneles import ejecutar_calculo_strings


@dataclass(frozen=True)
class PanelFV:
    voc_stc: float
    vmp_stc: float
    isc: float
    imp: float
    coef_voc_pct_c: float  # ej -0.28 (%/°C)
    pmax_w: float = 0.0


@dataclass(frozen=True)
class InversorFV:
    vdc_max: float
    mppt_min: float
    mppt_max: float
    imppt_max: float
    n_mppt: int
    pac_kw: float = 0.0


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _i(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return int(default)


def validar_string(
    panel: PanelFV,
    inversor: InversorFV,
    n_paneles_total: int,
    temp_min: float,
) -> Dict[str, Any]:
    """
    Wrapper UI:
    - NO llama al motor directo.
    - Llama al orquestador (un solo camino de ejecución).
    """
    warnings: List[str] = []
    errores: List[str] = []

    n_total = _i(n_paneles_total, 0)
    if n_total <= 0:
        return {
            "string_valido": False,
            "ok_vdc": False,
            "ok_mppt": False,
            "ok_corriente": False,
            "errores": ["n_paneles_total inválido (<=0)."],
            "warnings": [],
            "meta": {},
        }

    try:
        tmin = float(temp_min)
    except Exception:
        return {
            "string_valido": False,
            "ok_vdc": False,
            "ok_mppt": False,
            "ok_corriente": False,
            "errores": ["temp_min inválido (no convertible a número)."],
            "warnings": [],
            "meta": {},
        }

    # Ejecuta por el mismo pipeline estable
    res = ejecutar_calculo_strings(
        n_paneles_total=n_total,
        panel=panel,           # orquestador soporta voc_stc/vmp_stc/etc
        inversor=inversor,     # orquestador soporta vdc_max/mppt_min/mppt_max/etc
        t_min_c=tmin,
        dos_aguas=False,
        objetivo_dc_ac=None,
        pdc_kw_objetivo=None,
    ) or {}

    if not res.get("ok", False):
        return {
            "string_valido": False,
            "ok_vdc": False,
            "ok_mppt": False,
            "ok_corriente": False,
            "errores": list(res.get("errores") or []),
            "warnings": list(res.get("warnings") or []),
            "meta": res.get("meta") or {},
        }

    r = res.get("recomendacion") or {}

    voc_frio_total = _f(r.get("voc_frio_string_v", 0.0), 0.0)
    vmp_operativo = _f(r.get("vmp_string_v", 0.0), 0.0)

    # corriente: usar máximo i_mppt_a de strings[]
    i_mppt_max = 0.0
    for s in (res.get("strings") or []):
        i_mppt_max = max(i_mppt_max, _f(s.get("i_mppt_a", 0.0), 0.0))

    ok_vdc = (voc_frio_total > 0.0) and (voc_frio_total <= float(inversor.vdc_max) + 1e-9)
    ok_mppt = (vmp_operativo >= float(inversor.mppt_min) - 1e-9) and (vmp_operativo <= float(inversor.mppt_max) + 1e-9)
    ok_corr = i_mppt_max <= float(inversor.imppt_max) + 1e-9

    ns_recomendado = _i(r.get("n_series", r.get("n_paneles_string", r.get("ns", 0))), 0)
    n_strings_total = _i(r.get("n_strings_total", r.get("n_strings", 0)), 0)

    return {
        "voc_frio_total": voc_frio_total,
        "vmp_operativo": vmp_operativo,
        "corriente_mppt": float(i_mppt_max),
        "ok_vdc": bool(ok_vdc),
        "ok_mppt": bool(ok_mppt),
        "ok_corriente": bool(ok_corr),
        "string_valido": bool(ok_vdc and ok_mppt and ok_corr),
        "errores": [],
        "warnings": list(res.get("warnings") or []),
        "meta": {
            "n_paneles_total": n_total,
            "t_min_c": tmin,
            "ns_recomendado": ns_recomendado,
            "n_strings_total": n_strings_total,
            **(res.get("meta") or {}),
        },
    }
