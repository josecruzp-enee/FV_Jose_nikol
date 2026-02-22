# electrical/adaptador_nec.py
from __future__ import annotations

from typing import Any, Dict, List
import logging

from electrical.paquete_nec import armar_paquete_nec

logger = logging.getLogger(__name__)


def generar_electrico_nec(*, p: Any, sizing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adaptador Core → NEC.

    Contrato de salida:
      { ok: bool, errores: [..], input: {...}, paq: {...} }

    Nota:
      En esta versión, el input NEC se toma desde sizing["electrico"].
      (p se conserva por compatibilidad / futuras versiones.)
    """
    datos, errores = _extraer_input_desde_sizing(sizing)
    if errores:
        return {"ok": False, "errores": errores, "input": datos, "paq": {}}

    try:
        keys = list((sizing.get("electrico") or {}).keys())
    except Exception:
        keys = []
    logger.debug("NEC input desde sizing.electrico keys=%s", keys)

    return _ejecutar_nec(datos)


def _extraer_input_desde_sizing(sizing: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    electrico = sizing.get("electrico")
    if not electrico:
        return {}, ["NEC: sizing sin bloque 'electrico'"]

    datos = dict(electrico or {})

    # FIX: pasar n_paneles al motor NEC (para módulos por string)
    def _to_int(x: Any, default: int = 0) -> int:
        try:
            return int(float(x))
        except Exception:
            return default

    n_paneles = _to_int(sizing.get("n_paneles"), 0)
    if n_paneles <= 0:
        ps = sizing.get("panel_sizing") or {}
        if isinstance(ps, dict):
            n_paneles = _to_int(ps.get("n_paneles"), 0)

    if n_paneles > 0:
        datos["n_paneles"] = n_paneles

    req = ("n_strings", "isc_mod_a", "imp_mod_a", "vmp_string_v", "voc_frio_string_v", "p_ac_w")
    faltantes = [k for k in req if k not in datos or datos[k] in (None, 0)]

    if faltantes:
        return datos, [f"NEC: falta '{k}'" for k in faltantes]

    return datos, []


def _ejecutar_nec(datos: Dict[str, Any]) -> Dict[str, Any]:
    try:
        paq = armar_paquete_nec(datos)
        return {"ok": True, "errores": [], "input": datos, "paq": paq}
    except Exception as e:
        return {
            "ok": False,
            "errores": [f"NEC: {type(e).__name__}: {e}"],
            "input": datos,
            "paq": {},
        }
