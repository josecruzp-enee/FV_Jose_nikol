from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from electrical.modelos.paneles import PanelSpec as Panel
from electrical.modelos.inversor import InversorSpec as Inversor
from .catalogos_yaml import cargar_paneles_yaml, cargar_inversores_yaml


# ==========================================================
# Catálogo base (hardcoded) — opcional
# ==========================================================

_PANELES: Dict[str, Panel] = {
    "panel_550w": Panel(
        pmax_w=550.0,
        vmp_v=41.5,
        voc_v=49.5,
        imp_a=13.25,
        isc_a=14.10,
        coef_voc_pct_c=-0.28,
        coef_vmp_pct_c=-0.34,
    ),
}


_INVERSORES: Dict[str, Inversor] = {
    "inv_5kw_2mppt": Inversor(
        kw_ac=5.0,
        n_mppt=2,
        mppt_min_v=120.0,
        mppt_max_v=480.0,
        vdc_max_v=550.0,
        imppt_max_a=None,
    ),
}


_DATA_DIR = Path("data")
_YAML_PANELES = _DATA_DIR / "paneles.yaml"
_YAML_INVERSORES = _DATA_DIR / "inversores.yaml"


# ==========================================================
# Merge catálogo base + YAML
# ==========================================================

def _merge_paneles() -> Dict[str, Panel]:

    out = dict(_PANELES)

    if _YAML_PANELES.exists():
        out.update(cargar_paneles_yaml("paneles.yaml"))

    return out


def _merge_inversores() -> Dict[str, Inversor]:

    out = dict(_INVERSORES)

    if _YAML_INVERSORES.exists():
        out.update(cargar_inversores_yaml("inversores.yaml"))

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
            "modelo": pid,
            "pmax_w": float(p.pmax_w),
            "vmp_v": float(p.vmp_v),
            "voc_v": float(p.voc_v),
            "imp_a": float(p.imp_a),
            "isc_a": float(p.isc_a),
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
            "modelo": iid,
            "pac_kw": float(inv.kw_ac),
            "n_mppt": int(inv.n_mppt),
            "mppt_min_v": float(inv.mppt_min_v),
            "mppt_max_v": float(inv.mppt_max_v),
            "vmax_dc_v": float(inv.vdc_max_v),
        })

    return out
