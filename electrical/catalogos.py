# electrical/catalogos.py
from __future__ import annotations
from electrical.modelos import Panel, Inversor

def catalogo_paneles() -> list[dict]:
    """
    API para UI: lista de dicts con campos estándar.
    """
    out = []
    for nombre, p in PANELES.items():
        out.append({
            "id": nombre,
            "marca": "Genérico",
            "modelo": p.nombre if hasattr(p, "nombre") else nombre,
            "pmax_w": float(p.w),
            "vmp_v": float(p.vmp),
            "voc_v": float(p.voc),
            "imp_a": float(p.imp),
            "isc_a": float(p.isc),
        })
    return out


def catalogo_inversores() -> list[dict]:
    """
    API para UI: lista de dicts con campos estándar.
    """
    out = []
    for nombre, inv in INVERSORES.items():
        out.append({
            "id": nombre,
            "marca": "Genérico",
            "modelo": inv.nombre if hasattr(inv, "nombre") else nombre,
            "pac_kw": float(inv.kw_ac),
            "n_mppt": int(inv.n_mppt),
            "mppt_min_v": float(inv.vmppt_min),
            "mppt_max_v": float(inv.vmppt_max),
            "vmax_dc_v": float(inv.vdc_max),
        })
    return out

