from __future__ import annotations

from typing import Any, Dict, Mapping


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


def resumen_strings(res: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Resumen estable para UI/PDF.
    Tolera motor viejo/nuevo:
      - n_series / n_paneles_string / ns
      - n_strings_total / n_strings
      - strings_por_mppt
    """
    res = dict(res or {})
    r = res.get("recomendacion") or {}

    n_series = _i(r.get("n_series", r.get("n_paneles_string", r.get("ns", 0))), 0)
    n_strings_total = _i(r.get("n_strings_total", r.get("n_strings", 0)), 0)
    strings_por_mppt = _i(r.get("strings_por_mppt", 0), 0)

    out = {
        "ok": bool(res.get("ok", False)),
        "n_paneles_string": int(n_series),          # nombre legacy estable
        "n_series": int(n_series),                  # nombre nuevo estable
        "n_strings_total": int(n_strings_total),
        "strings_por_mppt": int(strings_por_mppt),
        "vmp_string_v": _f(r.get("vmp_string_v", 0.0), 0.0),
        "voc_frio_string_v": _f(r.get("voc_frio_string_v", 0.0), 0.0),
        "i_mppt_a": _f(r.get("i_mppt_a", 0.0), 0.0),
        "warnings": list(res.get("warnings") or []),
        "errores": list(res.get("errores") or []),
        "topologia": str(res.get("topologia") or ""),
        "meta": dict(res.get("meta") or {}),
    }

    return out
