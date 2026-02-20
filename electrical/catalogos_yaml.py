# electrical/catalogos.py
from __future__ import annotations

from typing import Dict, List, Optional

from .modelos import Panel, Inversor
from electrical.catalogos_yaml import cargar_paneles_yaml, cargar_inversores_yaml


_PANELES: Dict[str, Panel] = {
    "panel_550w": Panel(
        nombre="Panel 550 W (genérico)",
        w=550.0,
        vmp=41.5,
        voc=49.5,
        imp=13.25,
        isc=14.10,
    ),
}

_INVERSORES: Dict[str, Inversor] = {
    "inv_5kw_2mppt": Inversor(
        nombre="Inversor 5 kW (2 MPPT) genérico",
        kw_ac=5.0,
        n_mppt=2,
        vmppt_min=120.0,
        vmppt_max=480.0,
        vdc_max=550.0,
    ),
}


_PANELES_YAML: Optional[Dict[str, Panel]] = None
_INVERSORES_YAML: Optional[Dict[str, Inversor]] = None


def _paneles_yaml() -> Dict[str, Panel]:
    global _PANELES_YAML
    if _PANELES_YAML is None:
        _PANELES_YAML = cargar_paneles_yaml("paneles.yaml")
    return _PANELES_YAML


def _inversores_yaml() -> Dict[str, Inversor]:
    global _INVERSORES_YAML
    if _INVERSORES_YAML is None:
        _INVERSORES_YAML = cargar_inversores_yaml("inversores.yaml")
    return _INVERSORES_YAML


def get_panel(panel_id: str) -> Panel:
    paneles = _paneles_yaml()
    if panel_id in paneles:
        return paneles[panel_id]
    if panel_id in _PANELES:
        return _PANELES[panel_id]
    raise KeyError(f"Panel no existe en catálogo: {panel_id}")


def get_inversor(inv_id: str) -> Inversor:
    inversores = _inversores_yaml()
    if inv_id in inversores:
        return inversores[inv_id]
    if inv_id in _INVERSORES:
        return _INVERSORES[inv_id]
    raise KeyError(f"Inversor no existe en catálogo: {inv_id}")


def ids_paneles() -> List[str]:
    y = list(_paneles_yaml().keys())
    return sorted(y) if y else sorted(_PANELES.keys())


def ids_inversores() -> List[str]:
    y = list(_inversores_yaml().keys())
    return sorted(y) if y else sorted(_INVERSORES.keys())


def catalogo_paneles() -> List[dict]:
    paneles = _paneles_yaml() or _PANELES
    out: List[dict] = []
    for pid in sorted(paneles.keys()):
        p = paneles[pid]
        out.append({
            "id": pid,
            "marca": "YAML",
            "modelo": p.nombre,
            "pmax_w": float(p.w),
            "vmp_v": float(p.vmp),
            "voc_v": float(p.voc),
            "imp_a": float(p.imp),
            "isc_a": float(p.isc),
        })
    return out


def catalogo_inversores() -> List[dict]:
    inversores = _inversores_yaml() or _INVERSORES
    out: List[dict] = []
    for iid in sorted(inversores.keys()):
        inv = inversores[iid]
        out.append({
            "id": iid,
            "marca": "YAML",
            "modelo": inv.nombre,
            "pac_kw": float(inv.kw_ac),
            "n_mppt": int(inv.n_mppt),
            "mppt_min_v": float(inv.vmppt_min),
            "mppt_max_v": float(inv.vmppt_max),
            "vmax_dc_v": float(inv.vdc_max),
        })
    return out
