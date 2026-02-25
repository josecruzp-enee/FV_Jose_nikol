# Resumen del dominio paneles/strings: genera un shape estable para UI/PDF desde la salida del motor FV.
from __future__ import annotations

from typing import Any, Dict, Mapping


# Convierte cualquier valor a float seguro.
def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


# Convierte cualquier valor a entero seguro.
def _i(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return int(default)


# Extrae resumen estable independiente del formato interno del motor.
def resumen_strings(res: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Shape estable para UI/PDF.
    Tolera pequeñas variaciones del motor pero asume contrato moderno.
    """

    res = dict(res or {})
    r = res.get("recomendacion") if isinstance(res.get("recomendacion"), dict) else {}

    # ---- configuración básica ----
    n_series = _i(r.get("n_series", r.get("n_paneles_string", r.get("ns", 0))), 0)
    n_strings_total = _i(r.get("n_strings_total", r.get("n_strings", 0)), 0)
    strings_por_mppt = _i(r.get("strings_por_mppt", 0), 0)

    # ---- corrientes máximas observadas ----
    i_mppt_max = 0.0
    isc_array_max = 0.0
    imax_pv_max = 0.0
    idesign_cont_max = 0.0

    for s in (res.get("strings") or []):
        if not isinstance(s, dict):
            continue

        # corriente operativa
        i_mppt_max = max(i_mppt_max, _f(s.get("i_mppt_a"), 0.0))

        # valores normativos (si el motor los entrega)
        isc_array_max = max(isc_array_max, _f(s.get("isc_array_a"), 0.0))
        imax_pv_max = max(imax_pv_max, _f(s.get("imax_pv_a"), 0.0))
        idesign_cont_max = max(idesign_cont_max, _f(s.get("idesign_cont_a"), 0.0))

    # ---- salida estable ----
    return {
        "ok": bool(res.get("ok", False)),
        "n_paneles_string": int(n_series),
        "n_series": int(n_series),
        "n_strings_total": int(n_strings_total),
        "strings_por_mppt": int(strings_por_mppt),

        # voltajes (Vmp caliente es referencia operativa)
        "vmp_string_v": _f(r.get("vmp_string_v"), 0.0),
        "vmp_stc_string_v": _f(r.get("vmp_stc_string_v"), 0.0),
        "voc_frio_string_v": _f(r.get("voc_frio_string_v"), 0.0),

        # corrientes
        "i_mppt_a": float(i_mppt_max),
        "isc_array_a": float(isc_array_max),
        "imax_pv_a": float(imax_pv_max),
        "idesign_cont_a": float(idesign_cont_max),

        # estado
        "warnings": list(res.get("warnings") or []),
        "errores": list(res.get("errores") or []),
        "topologia": str(res.get("topologia") or ""),

        # trazabilidad completa
        "meta": dict(res.get("meta") or {}),
    }
