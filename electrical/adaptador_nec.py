# electrical/adaptador_nec.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from electrical.ingenieria_nec_2023 import calcular_paquete_electrico_nec


def generar_electrico_nec(*, p: Any, sizing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adaptador core -> NEC.
    Retorna dict estable:
      - ok: bool
      - errores: list[str]
      - (si ok) payload devuelto por calcular_paquete_electrico_nec()
    Nunca rompe el pipeline.
    """
    d, errores = _build_input_nec(p, sizing)
    if errores:
        return {"ok": False, "errores": errores, "input": d}

    try:
        paq = calcular_paquete_electrico_nec(d)
        # el módulo NEC ya suele incluir "resumen_pdf" y bloques dc/ac/protecciones/canalizacion
        return {"ok": True, "errores": [], **paq}
    except Exception as e:
        return {"ok": False, "errores": [f"NEC: {type(e).__name__}: {e}"], "input": d}


# ------------------------
# Builders (pequeños)
# ------------------------

def _build_input_nec(p: Any, sizing: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    d: Dict[str, Any] = {}
    d.update(_from_cfg_strings(sizing))
    d.update(_from_inversor_sizing(sizing))
    d.update(_defaults_proyecto(p))

    errores = _validar_minimos_nec(d)
    return d, errores


def _from_cfg_strings(sizing: Dict[str, Any]) -> Dict[str, Any]:
    cfg = (sizing or {}).get("cfg_strings") or {}
    strings = cfg.get("strings") or []
    if not strings:
        return {}

    # tu patrón actual: max() por seguridad
    vmp_string_v = _max_num(strings, "vmp_string_v")
    voc_string_v = _max_num(strings, "voc_string_v") or _max_num(strings, "voc_frio_v")  # fallback por si cambió key
    imp_a = _max_num(strings, "imp_a")
    isc_a = _max_num(strings, "isc_a")

    # cantidad de strings totales (en tu data actual: lista de strings)
    n_strings_total = len(strings)

    # iac estimada ya existe en cfg (la usas en electrico_ref)
    iac_estimada_a = cfg.get("iac_estimada_a", None)

    out: Dict[str, Any] = {
        "vmp_string_v": vmp_string_v,
        "voc_string_v": voc_string_v,
        "imp_a": imp_a,
        "isc_a": isc_a,
        "n_strings_total": n_strings_total,
    }
    if isinstance(iac_estimada_a, (int, float)) and float(iac_estimada_a) > 0:
        out["iac_estimada_a"] = float(iac_estimada_a)

    return out


def _from_inversor_sizing(sizing: Dict[str, Any]) -> Dict[str, Any]:
    """
    NEC requiere pac_w para calcular AC (si no viene iac directo).
    Intentamos encontrarlo en sizing con varios nombres sin romper.
    """
    s = sizing or {}

    # casos típicos: pac_kw, inv_kw_ac, kw_ac, etc.
    pac_kw = _first_num(s, ["pac_kw", "pac_kw_ac", "inv_kw_ac", "kw_ac", "p_ac_kw"])
    pac_w = _first_num(s, ["pac_w", "p_ac_w"])

    if pac_w is None and pac_kw is not None:
        pac_w = pac_kw * 1000.0

    out: Dict[str, Any] = {}
    if pac_w is not None and pac_w > 0:
        out["pac_w"] = float(pac_w)

    # opcional: si sizing trae sistema AC o fases
    sistema_ac = s.get("sistema_ac", None)
    if isinstance(sistema_ac, str) and sistema_ac.strip():
        out["sistema_ac"] = sistema_ac.strip()

    return out


def _defaults_proyecto(p: Any) -> Dict[str, Any]:
    """
    Defaults seguros. Si mañana los mapeas desde UI/config, aquí es el único lugar.
    """
    return {
        "sistema_ac": getattr(p, "sistema_ac", "1F-240V"),
        "pf": float(getattr(p, "fp", 1.0) or 1.0),

        "dist_dc_m": float(getattr(p, "dist_dc_m", 10.0) or 10.0),
        "dist_ac_m": float(getattr(p, "dist_ac_m", 15.0) or 15.0),
        "vd_obj_dc_pct": float(getattr(p, "vd_obj_dc_pct", 2.0) or 2.0),
        "vd_obj_ac_pct": float(getattr(p, "vd_obj_ac_pct", 2.0) or 2.0),

        "t_amb_c": float(getattr(p, "t_amb_c", 30.0) or 30.0),
        "material": getattr(p, "material_conductor", "Cu") or "Cu",

        # flags opcionales (si tu NEC los usa internamente)
        "spd": getattr(p, "spd", True),
        "seccionamiento": getattr(p, "seccionamiento", True),
    }


# ------------------------
# Validación mínima
# ------------------------

def _validar_minimos_nec(d: Dict[str, Any]) -> List[str]:
    req = [
        "vmp_string_v", "voc_string_v", "imp_a", "isc_a", "n_strings_total",
        "dist_dc_m", "vd_obj_dc_pct",
        "dist_ac_m", "vd_obj_ac_pct",
        "sistema_ac",
    ]

    errores: List[str] = []
    for k in req:
        if d.get(k, None) in (None, "", 0):
            errores.append(f"NEC: falta '{k}'")

    # AC: o pac_w o iac_estimada_a (para que NEC calcule conductor/protección AC)
    if (d.get("pac_w") in (None, 0)) and (d.get("iac_estimada_a") in (None, 0)):
        errores.append("NEC: falta 'pac_w' o 'iac_estimada_a'")

    return errores


# ------------------------
# Helpers pequeños
# ------------------------

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
