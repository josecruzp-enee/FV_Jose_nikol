from __future__ import annotations
from typing import Any, Dict, Mapping


def resumen_strings(res: Mapping[str, Any]) -> Dict[str, Any]:
    r = (res or {}).get("recomendacion") or {}
    return {
        "ok": bool(res.get("ok", False)),
        "n_paneles_string": int(r.get("n_paneles_string") or 0),
        "n_strings_total": int(r.get("n_strings_total") or 0),
        "strings_por_mppt": int(r.get("strings_por_mppt") or 0),
        "vmp_string_v": float(r.get("vmp_string_v") or 0.0),
        "voc_frio_string_v": float(r.get("voc_frio_string_v") or 0.0),
        "i_mppt_a": float(r.get("i_mppt_a") or 0.0),
        "warnings": list(res.get("warnings") or []),
        "errores": list(res.get("errores") or []),
        "topologia": str(res.get("topologia") or ""),
        "meta": dict(res.get("meta") or {}),
    }
