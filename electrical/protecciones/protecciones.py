# electrical/protecciones.py
from __future__ import annotations
from typing import Dict, Optional

TAMANOS_OCPD_STD = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200]

def siguiente_ocpd(a: float) -> int:
    x = float(a)
    for s in TAMANOS_OCPD_STD:
        if x <= s:
            return int(s)
    return int(TAMANOS_OCPD_STD[-1])

def breaker_ref(i_diseno_a: float) -> int:
    x = float(i_diseno_a)
    for b in [30, 40, 50, 60, 70, 80, 90, 100]:
        if x <= b:
            return int(b)
    return 125

def breaker_nec(iac_nom_a: float, factor: float = 1.25) -> Dict[str, float | int]:
    i_diseno = float(iac_nom_a) * float(factor)
    return {"i_diseno_a": round(i_diseno, 3), "tamano_a": siguiente_ocpd(i_diseno)}

def fusible_string_nec(*, n_strings: int, isc_mod_a: float, has_combiner: Optional[bool] = None) -> Dict[str, float | int | bool | str]:
    ns = int(n_strings); req = bool(has_combiner) if has_combiner is not None else (ns >= 3)
    if not req or ns < 3:
        return {"requerido": False, "nota": "Sin combiner o <3 strings en paralelo (verificar caso real)."}
    i_min = 1.25 * float(isc_mod_a)
    return {"requerido": True, "i_min_a": round(i_min, 3), "tamano_a": siguiente_ocpd(i_min)}

def dimensionar_protecciones_fv(*, iac_nom_a: float, n_strings: int, isc_mod_a: float, has_combiner: Optional[bool] = None) -> Dict[str, object]:
    return {
        "breaker_ac": breaker_nec(iac_nom_a),
        "fusible_string": fusible_string_nec(n_strings=n_strings, isc_mod_a=isc_mod_a, has_combiner=has_combiner),
    }
