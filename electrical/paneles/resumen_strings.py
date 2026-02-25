# Resumen del dominio paneles/strings: extrae un “shape” estable para UI/PDF desde la salida del motor/orquestador.
from __future__ import annotations

from typing import Any, Dict, Mapping


# Convierte cualquier valor a float seguro usando un valor por defecto.
def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


# Convierte cualquier valor a entero seguro usando un valor por defecto.
def _i(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return int(default)


# Construye un resumen estable (compatible) para UI/PDF a partir del resultado completo de strings.
def resumen_strings(res: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Resumen estable para UI/PDF.
    Tolera motor viejo/nuevo:
      - n_series / n_paneles_string / ns
      - n_strings_total / n_strings
      - strings_por_mppt
      - vmp_string_v (ahora Vmp caliente)
    """
    res = dict(res or {})
    r = (res.get("recomendacion") or {}) if isinstance(res.get("recomendacion"), dict) else {}

    n_series = _i(r.get("n_series", r.get("n_paneles_string", r.get("ns", 0))), 0)
    n_strings_total = _i(r.get("n_strings_total", r.get("n_strings", 0)), 0)
    strings_por_mppt = _i(r.get("strings_por_mppt", 0), 0)

    # Corriente MPPT: usamos el máximo reportado por rama (operativa) si existe.
    i_mppt_max = 0.0
    for s in (res.get("strings") or []):
        if isinstance(s, dict):
            i_mppt_max = max(i_mppt_max, _f(s.get("i_mppt_a", 0.0), 0.0))

    # Corrientes "a norma": preferimos Imax_pv (1.25*Isc_array) y el diseño continuo (1.56*Isc_array) si vienen.
    imax_pv_max = 0.0
    idesign_cont_max = 0.0
    isc_array_max = 0.0
    for s in (res.get("strings") or []):
        if isinstance(s, dict):
            isc_array_max = max(isc_array_max, _f(s.get("isc_array_a", 0.0), 0.0))
            imax_pv_max = max(imax_pv_max, _f(s.get("imax_pv_a", 0.0), 0.0))
            idesign_cont_max = max(idesign_cont_max, _f(s.get("idesign_cont_a", 0.0), 0.0))

    out = {
        "ok": bool(res.get("ok", False)),
        "n_paneles_string": int(n_series),
        "n_series": int(n_series),
        "n_strings_total": int(n_strings_total),
        "strings_por_mppt": int(strings_por_mppt),
        # Voltajes: vmp_string_v es Vmp caliente (MPPT_min check); guardamos trazabilidad si existe.
        "vmp_string_v": _f(r.get("vmp_string_v", 0.0), 0.0),
        "vmp_stc_string_v": _f(r.get("vmp_stc_string_v", 0.0), 0.0),
        "voc_frio_string_v": _f(r.get("voc_frio_string_v", 0.0), 0.0),
        # Corrientes: operativa y normativas (si el motor las entrega).
        "i_mppt_a": float(i_mppt_max),
        "isc_array_a": float(isc_array_max),
        "imax_pv_a": float(imax_pv_max),
        "idesign_cont_a": float(idesign_cont_max),
        "warnings": list(res.get("warnings") or []),
        "errores": list(res.get("errores") or []),
        "topologia": str(res.get("topologia") or ""),
        "meta": dict(res.get("meta") or {}),
    }

    return out
