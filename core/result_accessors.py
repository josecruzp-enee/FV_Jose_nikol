from __future__ import annotations

from typing import Any, Dict, List

__all__ = [
    "as_float",
    "as_int",
    "get_sizing",
    "get_kwp_dc",
    "get_capex_L",
    "get_n_paneles",
    "get_tabla_12m",
    "get_consumo_anual",
    "get_electrico_nec",
    "get_electrico_nec_pkg",
    "get_strings",
]


# ==========================================================
# Helpers base
# ==========================================================
def _as_dict(x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return dict(x)
    # soporte dataclass/obj con __dict__
    if hasattr(x, "__dict__"):
        try:
            d = getattr(x, "__dict__", {}) or {}
            return dict(d) if isinstance(d, dict) else {}
        except Exception:
            return {}
    return {}


def _pick_root(res: Any) -> Dict[str, Any]:
    """
    Normaliza "root" para soportar:
      - dict legacy: {sizing, tabla_12m, electrico_nec, ...}
      - dict nuevo:  {tecnico:{...}, financiero:{...}, ...}
      - dataclass ResultadoProyecto (con __dict__)
    """
    r = _as_dict(res)
    if "tecnico" in r and isinstance(r.get("tecnico"), dict):
        # contrato nuevo
        return r
    return r


def as_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def as_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return int(default)
        return int(float(x))
    except Exception:
        return int(default)


def _get_tecnico(res: Any) -> Dict[str, Any]:
    r = _pick_root(res)
    tec = r.get("tecnico")
    return _as_dict(tec) if isinstance(tec, dict) else {}


def _get_financiero(res: Any) -> Dict[str, Any]:
    r = _pick_root(res)
    fin = r.get("financiero")
    return _as_dict(fin) if isinstance(fin, dict) else {}


# ==========================================================
# Accessors
# ==========================================================
def get_sizing(res: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    Compat:
      - legacy: res["sizing"]
      - nuevo:   res["tecnico"]["sizing"]
    """
    r = _pick_root(res)
    if "tecnico" in r and isinstance(r.get("tecnico"), dict):
        return _as_dict(_get_tecnico(r).get("sizing"))
    return _as_dict(r.get("sizing"))


def get_kwp_dc(res: Dict[str, Any] | None) -> float:
    sizing = get_sizing(res)
    return as_float(
        sizing.get("kwp_dc")
        or sizing.get("kwp_recomendado")
        or sizing.get("kwp")
        or sizing.get("pdc_kw")
        or 0.0
    )


def get_capex_L(res: Dict[str, Any] | None) -> float:
    sizing = get_sizing(res)
    return as_float(sizing.get("capex_L") or sizing.get("capex") or 0.0)


def get_n_paneles(res: Dict[str, Any] | None) -> int:
    sizing = get_sizing(res)

    n = as_int(sizing.get("n_paneles"), 0)
    if n > 0:
        return n

    cfg = _as_dict(sizing.get("cfg_strings"))
    return as_int(cfg.get("n_paneles") or cfg.get("n_modulos") or cfg.get("n_paneles_total") or 0, 0)


def get_tabla_12m(res: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    """
    Compat:
      - legacy: res["tabla_12m"]
      - nuevo:  res["tecnico"]["tabla_12m"]  (o financiero si lo mueves)
    """
    r = _pick_root(res)

    t = r.get("tabla_12m")
    if not isinstance(t, list) and "tecnico" in r:
        t = _get_tecnico(r).get("tabla_12m")

    # fallback: si alguien la guarda en financiero
    if not isinstance(t, list) and "financiero" in r:
        t = _get_financiero(r).get("tabla_12m")

    if not isinstance(t, list):
        return []

    out: List[Dict[str, Any]] = []
    for row in t:
        if isinstance(row, dict):
            out.append(dict(row))
    return out


def get_consumo_anual(res: Dict[str, Any] | None, datos: Any = None) -> float:
    tabla = get_tabla_12m(res)
    if tabla:
        total = 0.0
        for row in tabla:
            total += as_float(row.get("consumo_kwh") or row.get("consumo_mes_kwh") or 0.0)
        if total > 0:
            return float(total)

    if datos is not None:
        consumo_12m = getattr(datos, "consumo_12m", None) or getattr(datos, "consumo_mensual_kwh", None)
        if isinstance(consumo_12m, list):
            return float(sum(as_float(x, 0.0) for x in consumo_12m))

    return 0.0


def get_electrico_nec(res: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    Compat:
      - legacy: res["electrico_nec"]
      - nuevo:  res["tecnico"]["electrico_nec"]
    """
    r = _pick_root(res)
    if "tecnico" in r and isinstance(r.get("tecnico"), dict):
        return _as_dict(_get_tecnico(r).get("electrico_nec"))
    return _as_dict(r.get("electrico_nec"))


def get_electrico_nec_pkg(res: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    Devuelve el paquete NEC (paq).

    Compat extra:
      - si el PDF/UI metió paq directo como res["electrico"], también lo tomamos.
    """
    # 1) forma estándar: electrico_nec.paq
    nec = get_electrico_nec(res)
    paq = _as_dict(nec.get("paq"))
    if paq:
        return paq

    # 2) forma inyectada en PDF/UI: res["electrico"] = paq
    r = _pick_root(res)
    e = r.get("electrico")
    if isinstance(e, dict) and isinstance(e.get("dc"), dict):
        return _as_dict(e)

    # 3) nuevo: res["tecnico"]["electrico"] = paq
    if "tecnico" in r:
        tec = _get_tecnico(r)
        e2 = tec.get("electrico")
        if isinstance(e2, dict) and isinstance(e2.get("dc"), dict):
            return _as_dict(e2)

    return {}


def get_strings(res: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    """
    Prioridad:
      1) sizing.cfg_strings.strings (si existen)
      2) NEC paq.dc.config_strings (fallback mínimo)
    """
    sizing = get_sizing(res)
    cfg = _as_dict(sizing.get("cfg_strings"))
    strings = cfg.get("strings")
    if isinstance(strings, list):
        return [dict(s) for s in strings if isinstance(s, dict)]

    paq = get_electrico_nec_pkg(res)
    dc = _as_dict(paq.get("dc"))
    c = _as_dict(dc.get("config_strings"))
    if as_int(c.get("n_strings"), 0) <= 0:
        return []

    return [{
        "mppt": 1,
        "n_series": as_int(c.get("modulos_por_string"), 0),
        "n_paralelo": as_int(c.get("n_strings"), 0),
        "vmp_string_v": as_float(dc.get("vmp_string_v"), 0.0),
        "voc_string_frio_v": as_float(dc.get("voc_frio_string_v"), 0.0),
        "imp_a": as_float(dc.get("i_string_oper_a"), 0.0),
        "isc_a": as_float(dc.get("i_array_isc_a"), 0.0),
    }]


# Backward-compatible aliases (internal callers previos)
_as_float = as_float
_as_int = as_int
