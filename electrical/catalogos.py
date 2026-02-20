# electrical/catalogos.py
from __future__ import annotations
from dataclasses import replace
from typing import Dict, List
from .modelos import Panel, Inversor
from electrical.catalogos_yaml import cargar_paneles_yaml, cargar_inversores_yaml
from pathlib import Path

# ==========================================================
# Fuente de verdad: catálogos en objetos (NO UI dicts)
# ==========================================================

_PANELES: Dict[str, Panel] = {
    # 🔻 Pon aquí tu catálogo real. Estos son ejemplos "genéricos".
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


# ==========================================================
# API pública para el resto del sistema
# ==========================================================

def get_panel(panel_id):
    try:
        return PANELES[panel_id]
    except Exception as e:
        # fallback a YAML
        if _YAML_PANELES.exists():
            paneles = cargar_paneles_yaml(_YAML_PANELES)
            if panel_id in paneles:
                return paneles[panel_id]
        raise KeyError(f"Panel no existe en catálogo: {panel_id}") from e

def get_inversor(inv_id: str):
    try:
        return INVERSORES[inv_id]
    except Exception as e:
        # fallback YAML
        if _YAML_INVERSORES.exists():
            inversores = cargar_inversores_yaml(_YAML_INVERSORES)
            if inv_id in inversores:
                return inversores[inv_id]

        raise KeyError(f"Inversor no existe en catálogo: {inv_id}") from e


def ids_paneles() -> List[str]:
    return sorted(_PANELES.keys())


def ids_inversores() -> List[str]:
    return sorted(_INVERSORES.keys())


# ==========================================================
# API para UI (listas de dicts estandarizados)
# ==========================================================

def catalogo_paneles() -> list[dict]:
    out: list[dict] = []
    for pid in ids_paneles():
        p = _PANELES[pid]
        out.append({
            "id": pid,
            "marca": "Genérico",
            "modelo": p.nombre,
            "pmax_w": float(p.w),
            "vmp_v": float(p.vmp),
            "voc_v": float(p.voc),
            "imp_a": float(p.imp),
            "isc_a": float(p.isc),
        })
    return out


def catalogo_inversores() -> list[dict]:
    out: list[dict] = []
    for iid in ids_inversores():
        inv = _INVERSORES[iid]
        out.append({
            "id": iid,
            "marca": "Genérico",
            "modelo": inv.nombre,
            "pac_kw": float(inv.kw_ac),
            "n_mppt": int(inv.n_mppt),
            "mppt_min_v": float(inv.vmppt_min),
            "mppt_max_v": float(inv.vmppt_max),
            "vmax_dc_v": float(inv.vdc_max),
        })
    return out
