# electrical/catalogos.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .modelos import Panel, Inversor
from .catalogos_yaml import cargar_paneles_yaml, cargar_inversores_yaml

# ==========================================================
# Catálogo base (hardcoded) — opcional
# ==========================================================

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
        vdc_max_v=550.0,
    ),
}

_DATA_DIR = Path("data")
_YAML_PANELES = _DATA_DIR / "paneles.yaml"
_YAML_INVERSORES = _DATA_DIR / "inversores.yaml"


def _merge_paneles() -> Dict[str, Panel]:
    out = dict(_PANELES)
    if _YAML_PANELES.exists():
        out.update(cargar_paneles_yaml("paneles.yaml"))  # devuelve Dict[str, Panel]
    return out


def _merge_inversores() -> Dict[str, Inversor]:
    out = dict(_INVERSORES)
    if _YAML_INVERSORES.exists():
        out.update(cargar_inversores_yaml("inversores.yaml"))  # devuelve Dict[str, Inversor]
    return out


# ==========================================================
# API pública (fuente de verdad)
# ==========================================================

def get_panel(panel_id: str) -> Panel:
    paneles = _merge_paneles()
    if panel_id in paneles:
        return paneles[panel_id]
    raise KeyError(f"Panel no existe en catálogo: {panel_id}")


def get_inversor(inv_id: str) -> Inversor:
    inversores = _merge_inversores()
    if inv_id in inversores:
        return inversores[inv_id]
    raise KeyError(f"Inversor no existe en catálogo: {inv_id}")


def ids_paneles() -> List[str]:
    return sorted(_merge_paneles().keys())


def ids_inversores() -> List[str]:
    return sorted(_merge_inversores().keys())


# ==========================================================
# API para UI (listas de dicts)
# ==========================================================

def catalogo_paneles() -> list[dict]:
    paneles = _merge_paneles()
    out: list[dict] = []
    for pid in sorted(paneles.keys()):
        p = paneles[pid]
        out.append({
            "id": pid,
            "marca": "YAML/Base",
            "modelo": p.nombre,
            "pmax_w": float(p.w),
            "vmp_v": float(p.vmp),
            "voc_v": float(p.voc),
            "imp_a": float(p.imp),
            "isc_a": float(p.isc),
        })
    return out


def catalogo_inversores() -> list[dict]:
    inversores = _merge_inversores()
    out: list[dict] = []
    for iid in sorted(inversores.keys()):
        inv = inversores[iid]
        out.append({
            "id": iid,
            "marca": "YAML/Base",
            "modelo": inv.nombre,
            "pac_kw": float(inv.kw_ac),
            "n_mppt": int(inv.n_mppt),
            "mppt_min_v": float(inv.vmppt_min),
            "mppt_max_v": float(inv.vmppt_max),
            "vmax_dc_v": float(inv.vdc_max_v),
        })
    return out
