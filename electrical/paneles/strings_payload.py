from __future__ import annotations
from typing import Any, Dict


def build_strings_payload(*, panel: Any, inversor: Any, n_paneles_total: int, t_min_c: float, dos_aguas: bool) -> Dict[str, Any]:
    return {
        "n_paneles_total": int(n_paneles_total),
        "t_min_c": float(t_min_c),
        "dos_aguas": bool(dos_aguas),
        "panel": panel,
        "inversor": inversor,
    }
