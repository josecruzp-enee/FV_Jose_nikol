from __future__ import annotations

from typing import Any, Dict


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


def build_strings_payload(
    *,
    panel: Any,
    inversor: Any,
    n_paneles_total: int,
    t_min_c: float,
    dos_aguas: bool,
) -> Dict[str, Any]:
    """
    Normaliza entradas provenientes de UI / Excel / API externa.

    - NO hace cálculos eléctricos.
    - NO valida NEC.
    - Solo empaqueta tipos/valores básicos para el orquestador.
    """
    return {
        "n_paneles_total": _i(n_paneles_total, 0),
        "t_min_c": _f(t_min_c, 0.0),
        "dos_aguas": bool(dos_aguas),
        "panel": panel,
        "inversor": inversor,
    }
