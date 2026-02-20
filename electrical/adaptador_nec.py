# electrical/adaptador_nec.py
from __future__ import annotations
from typing import Any, Dict, List, Tuple

from electrical.ingenieria_nec_2023 import calcular_paquete_electrico_nec

def generar_electrico_nec(*, p: Any, sizing: Dict[str, Any]) -> Dict[str, Any]:
    d = _build_nec_input(p, sizing)
    if d["errores"]:
        return {"ok": False, "errores": d["errores"], "input": d["input"]}
    try:
        paq = calcular_paquete_electrico_nec(d["input"])
        return {"ok": True, "errores": [], **paq}
    except Exception as e:
        return {"ok": False, "errores": [f"NEC: {type(e).__name__}: {e}"], "input": d["input"]}

def _build_nec_input(p: Any, sizing: Dict[str, Any]) -> Dict[str, Any]:
    inp: Dict[str, Any] = {}

    # 1) extraer base desde sizing (panel/inversor/strings)
    inp.update(_nec_from_sizing(sizing))

    # 2) completar con defaults del proyecto (distancias, temp, objetivos VD, sistema AC)
    inp.update(_nec_from_proyecto(p, sizing))

    # 3) validar mínimos (sin reventar)
    errores = _validar_minimos(inp)
    return {"input": inp, "errores": errores}

def _nec_from_sizing(sizing: Dict[str, Any]) -> Dict[str, Any]:
    # TODO: mapear keys reales de tu sizing (abajo te dejo el contrato)
    return {}

def _nec_from_proyecto(p: Any, sizing: Dict[str, Any]) -> Dict[str, Any]:
    return {
        # defaults seguros; NEC también tiene _defaults(d)
        "t_amb_c": getattr(p, "t_amb_c", 30.0),
        "pf": getattr(p, "fp", 1.0),
        "vd_obj_dc_pct": getattr(p, "vd_obj_dc_pct", 2.0),
        "vd_obj_ac_pct": getattr(p, "vd_obj_ac_pct", 2.0),
        "dist_dc_m": getattr(p, "dist_dc_m", 10.0),
        "dist_ac_m": getattr(p, "dist_ac_m", 15.0),
        "material": getattr(p, "material_conductor", "Cu"),
        "sistema_ac": getattr(p, "sistema_ac", "1F-240V"),
    }

def _validar_minimos(d: Dict[str, Any]) -> List[str]:
    req = [
        "vmp_string_v", "voc_string_v", "isc_a", "imp_a", "n_strings_total",
        "pac_w", "sistema_ac", "dist_dc_m", "dist_ac_m",
    ]
    faltan = [k for k in req if d.get(k, None) in (None, "", 0)]
    return [f"Falta '{k}' para NEC" for k in faltan]
