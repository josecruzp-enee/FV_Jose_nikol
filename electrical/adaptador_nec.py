# electrical/adaptador_nec.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import logging

from electrical.paquete_nec import armar_paquete_nec

logger = logging.getLogger(__name__)


# ==========================================================
# Adapter core -> NEC
# ==========================================================
def generar_electrico_nec(*, p: Any, sizing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adaptador Core → NEC.

    Contrato de salida:
      { ok: bool, errores: [..], input: {...}, paq: {...} }

    Nota: En esta versión inicial, el input NEC se extrae desde:
      sizing["electrico"]
    (p se conserva para futuras versiones donde se construya el input
     desde el proyecto + sizing con un builder más completo.)
    """
    datos, errores = _extraer_input_desde_sizing(sizing)

    if errores:
        return {"ok": False, "errores": errores, "input": datos, "paq": {}}

    # log seguro (no imprime todo el dict)
    try:
        keys = list((sizing.get("electrico") or {}).keys())
    except Exception:
        keys = []
    logger.debug("NEC input desde sizing.electrico keys=%s", keys)

    return _ejecutar_nec(datos)


# ==========================================================
# 1) Construcción input NEC desde sizing["electrico"]
# ==========================================================
def _extraer_input_desde_sizing(sizing: Dict[str, Any]):
    electrico = sizing.get("electrico")
    if not electrico:
        return {}, ["NEC: sizing sin bloque 'electrico'"]

    datos = dict(electrico or {})

    # ----------------------------------------------------------
    # FIX: pasar n_paneles al motor NEC (para módulos por string)
    # Preferencia:
    #   1) sizing["n_paneles"]
    #   2) sizing["panel_sizing"]["n_paneles"]
    # ----------------------------------------------------------
    def _to_int(x: Any, default: int = 0) -> int:
        try:
            return int(float(x))
        except Exception:
            return default

    n_paneles = _to_int(sizing.get("n_paneles"), 0)
    if n_paneles <= 0:
        ps = (sizing.get("panel_sizing") or {})
        if isinstance(ps, dict):
            n_paneles = _to_int(ps.get("n_paneles"), 0)

    if n_paneles > 0:
        datos["n_paneles"] = n_paneles

    faltantes = [
        k
        for k in (
            "n_strings",
            "isc_mod_a",
            "imp_mod_a",
            "vmp_string_v",
            "voc_frio_string_v",
            "p_ac_w",
        )
        if k not in datos or datos[k] in (None, 0)
    ]

    if faltantes:
        return datos, [f"NEC: falta '{k}'" for k in faltantes]

    return datos, []


# ==========================================================
# 2) Ejecución NEC segura
# ==========================================================
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


# ==========================================================
# Builders alternos (no usados en esta versión)
#   - Los dejo intactos para que luego migres a construir input NEC
#     desde (p + sizing) sin depender de sizing["electrico"].
# ==========================================================
def _build_input_nec(p: Any, sizing: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    d: Dict[str, Any] = {}

    d.update(_from_cfg_strings(sizing))
    d.update(_from_p_ac_w(sizing))
    d.update(_defaults_desde_proyecto(p, sizing))

    errores = _validar_minimos_nec(d)
    return d, errores


def _from_cfg_strings(sizing: Dict[str, Any]) -> Dict[str, Any]:
    cfg = (sizing or {}).get("cfg_strings") or {}
    strings = cfg.get("strings") or []
    if not strings:
        return {}

    vmp = _max_num(strings, "vmp_string_v")
    imp = _max_num(strings, "imp_a")
    isc = _max_num(strings, "isc_a")

    voc_frio = (
        _max_num(strings, "voc_frio_string_v")
        or _max_num(strings, "voc_frio_v")
        or _max_num(strings, "voc_string_v")
        or _max_num(strings, "voc_v")
    )

    out: Dict[str, Any] = {
        "n_strings": len(strings),
        "isc_mod_a": isc,
        "imp_mod_a": imp,
        "vmp_string_v": vmp,
        "voc_frio_string_v": voc_frio,
    }

    iac = cfg.get("iac_estimada_a", None)
    if isinstance(iac, (int, float)) and float(iac) > 0:
        out["iac_estimada_a"] = float(iac)

    return out


def _from_p_ac_w(sizing: Dict[str, Any]) -> Dict[str, Any]:
    s = sizing or {}

    p_ac_w = _first_num(s, ["p_ac_w", "pac_w"])
    pac_kw = _first_num(s, ["pac_kw", "pac_kw_ac", "inv_kw_ac", "kw_ac", "p_ac_kw"])

    if p_ac_w is None and pac_kw is not None:
        p_ac_w = pac_kw * 1000.0

    return {"p_ac_w": float(p_ac_w)} if (p_ac_w is not None and p_ac_w > 0) else {}


def _defaults_desde_proyecto(p: Any, sizing: Dict[str, Any]) -> Dict[str, Any]:
    eq = getattr(p, "equipos", None) or {}

    tension = (
        eq.get("tension_sistema")
        or getattr(p, "tension_sistema", None)
        or getattr(p, "sistema_ac", None)
        or "1F_240V"
    )

    return {
        "tension_sistema": _normalizar_tag_sistema_ac(str(tension)),

        "pf_ac": float(getattr(p, "fp", 1.0) or 1.0),

        "vd_max_dc_pct": float(getattr(p, "vd_obj_dc_pct", 2.0) or 2.0),
        "vd_max_ac_pct": float(getattr(p, "vd_obj_ac_pct", 2.0) or 2.0),

        "L_dc_string_m": float(getattr(p, "dist_dc_m", 10.0) or 10.0),
        "L_dc_trunk_m": float(getattr(p, "L_dc_trunk_m", 0.0) or 0.0),
        "L_ac_m": float(getattr(p, "dist_ac_m", 15.0) or 15.0),

        "material": getattr(p, "material_conductor", "Cu") or "Cu",
        "temp_amb_c": float(getattr(p, "t_amb_c", 30.0) or 30.0),

        "has_combiner": bool(getattr(p, "has_combiner", False)),
        "dc_arch": getattr(p, "dc_arch", "string_to_inverter") or "string_to_inverter",
    }


# ==========================================================
# Validación mínima
# ==========================================================
def _validar_minimos_nec(d: Dict[str, Any]) -> List[str]:
    req = [
        "tension_sistema",
        "n_strings",
        "isc_mod_a",
        "imp_mod_a",
        "vmp_string_v",
        "voc_frio_string_v",
        "p_ac_w",
        "L_dc_string_m",
        "L_ac_m",
        "vd_max_dc_pct",
        "vd_max_ac_pct",
    ]

    errores: List[str] = []
    for k in req:
        v = d.get(k, None)
        if v in (None, "", 0):
            errores.append(f"NEC: falta '{k}'")

    return errores


# ==========================================================
# Helpers pequeños
# ==========================================================
def _max_num(items: List[Dict[str, Any]], key: str) -> Optional[float]:
    vals: List[float] = []
    for it in items:
        v = it.get(key, None)
        if isinstance(v, (int, float)):
            vals.append(float(v))
    return max(vals) if vals else None


def _first_num(d: Dict[str, Any], keys: List[str]) -> Optional[float]:
    for k in keys:
        v = d.get(k, None)
        if isinstance(v, (int, float)) and float(v) > 0:
            return float(v)
    return None


def _normalizar_tag_sistema_ac(tag: str) -> str:
    t = (tag or "").strip()

    if t in ("1F-240V", "1F_240", "1F240", "240V_1F"):
        return "1F_240V"
    if t in ("2F+N-120/240", "2F+N_120/240", "120/240", "1F_120/240"):
        return "2F+N_120/240"
    if t in ("3F+N-120/208", "3F+N_120/208", "208Y/120", "3F_208Y120V"):
        return "3F+N_120/208"
    if t in ("3F_480Y277", "3F+N_480Y277", "480Y/277"):
        return "3F_480Y277V"

    return t if t else "1F_240V"
