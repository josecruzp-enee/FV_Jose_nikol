from __future__ import annotations

from typing import Any, Dict, List


def _as_dict(x: Any) -> Dict[str, Any]:
    return dict(x) if isinstance(x, dict) else {}


def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def _as_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return int(default)
        return int(float(x))
    except Exception:
        return int(default)


def get_sizing(res: Dict[str, Any] | None) -> Dict[str, Any]:
    return _as_dict((res or {}).get("sizing"))


def get_kwp_dc(res: Dict[str, Any] | None) -> float:
    sizing = get_sizing(res)
    return _as_float(
        sizing.get("kwp_dc")
        or sizing.get("kwp_recomendado")
        or sizing.get("kwp")
        or sizing.get("pdc_kw")
        or 0.0
    )


def get_capex_L(res: Dict[str, Any] | None) -> float:
    sizing = get_sizing(res)
    return _as_float(sizing.get("capex_L") or sizing.get("capex") or 0.0)


def get_n_paneles(res: Dict[str, Any] | None) -> int:
    sizing = get_sizing(res)
    n = _as_int(sizing.get("n_paneles"), 0)
    if n > 0:
        return n

    cfg = _as_dict(sizing.get("cfg_strings"))
    return _as_int(cfg.get("n_paneles") or cfg.get("n_modulos") or cfg.get("n_paneles_total") or 0, 0)


def get_tabla_12m(res: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    t = (res or {}).get("tabla_12m")
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
            total += _as_float(row.get("consumo_kwh") or row.get("consumo_mes_kwh") or 0.0)
        if total > 0:
            return float(total)

    if datos is not None:
        consumo_12m = getattr(datos, "consumo_12m", None) or getattr(datos, "consumo_mensual_kwh", None)
        if isinstance(consumo_12m, list):
            return float(sum(_as_float(x, 0.0) for x in consumo_12m))

    return 0.0


def get_electrico_nec(res: Dict[str, Any] | None) -> Dict[str, Any]:
    return _as_dict((res or {}).get("electrico_nec"))


def get_electrico_nec_pkg(res: Dict[str, Any] | None) -> Dict[str, Any]:
    nec = get_electrico_nec(res)
    return _as_dict(nec.get("paq"))


def get_strings(res: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    sizing = get_sizing(res)
    cfg = _as_dict(sizing.get("cfg_strings"))
    strings = cfg.get("strings")
    if isinstance(strings, list):
        return [dict(s) for s in strings if isinstance(s, dict)]

    paq = get_electrico_nec_pkg(res)
    dc = _as_dict(paq.get("dc"))
    c = _as_dict(dc.get("config_strings"))
    if _as_int(c.get("n_strings"), 0) <= 0:
        return []

    return [{
        "mppt": 1,
        "n_series": _as_int(c.get("modulos_por_string"), 0),
        "n_paralelo": _as_int(c.get("n_strings"), 0),
        "vmp_string_v": _as_float(dc.get("vmp_string_v"), 0.0),
        "voc_string_frio_v": _as_float(dc.get("voc_frio_string_v"), 0.0),
        "imp_a": _as_float(dc.get("i_string_oper_a"), 0.0),
        "isc_a": _as_float(dc.get("i_array_isc_a"), 0.0),
    }]
