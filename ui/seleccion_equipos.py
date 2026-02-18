from __future__ import annotations
from typing import List, Tuple
import streamlit as st

from electrical.catalogos import catalogo_paneles, catalogo_inversores


def _defaults(ctx):
    if not ctx.equipos:
        ctx.equipos = {
            "panel_id": None,
            "inversor_id": None,
            "sobredimension_dc_ac": 1.20,
            "tension_sistema": "1F_240V",
        }


def render(ctx):
    _defaults(ctx)
    e = ctx.equipos

    st.markdown("### Selección de equipos")

    # ===== Cargar catálogos =====
    paneles = catalogo_paneles()      # debe devolver dict/list
    inversores = catalogo_inversores()

    # Normalización simple: dict {id: obj}
    panel_map = {p["id"]: p for p in paneles}
    inv_map   = {i["id"]: i for i in inversores}

    col1, col2 = st.columns(2)

    with col1:
        e["panel_id"] = st.selectbox(
            "Panel FV",
            options=list(panel_map.keys()),
            index=0 if e["panel_id"] is None else list(panel_map.keys()).index(e["panel_id"]),
            format_func=lambda pid: f'{panel_map[pid]["marca"]} {panel_map[pid]["modelo"]} ({panel_map[pid]["pmax_w"]} W)',
        )

    with col2:
        e["inversor_id"] = st.selectbox(
            "Inversor",
            options=list(inv_map.keys()),
            index=0 if e["inversor_id"] is None else list(inv_map.keys()).index(e["inversor_id"]),
            format_func=lambda iid: f'{inv_map[iid]["marca"]} {inv_map[iid]["modelo"]} ({inv_map[iid]["pac_kw"]} kW)',
        )

    st.markdown("#### Criterios")

    a, b = st.columns(2)
    with a:
        e["sobredimension_dc_ac"] = st.number_input(
            "Objetivo DC/AC",
            min_value=1.0,
            max_value=1.6,
            step=0.05,
            value=float(e.get("sobredimension_dc_ac", 1.20)),
        )
    with b:
        e["tension_sistema"] = st.selectbox(
            "Tensión del sistema",
            options=["1F_240V", "3F_208Y120V", "3F_480Y277V"],
            index=["1F_240V", "3F_208Y120V", "3F_480Y277V"].index(e.get("tension_sistema", "1F_240V")),
        )

    # ===== Preview técnico rápido (sin cálculos) =====
    st.markdown("#### Resumen técnico")
    p = panel_map[e["panel_id"]]
    inv = inv_map[e["inversor_id"]]

    st.write(f"**Panel:** {p['marca']} {p['modelo']} — Pmax {p['pmax_w']} W, Voc {p['voc_v']} V")
    st.write(f"**Inversor:** {inv['marca']} {inv['modelo']} — AC {inv['pac_kw']} kW, MPPT {inv['mppt_min_v']}-{inv['mppt_max_v']} V")

    ctx.equipos = e


def validar(ctx) -> Tuple[bool, List[str]]:
    e = []
    eq = ctx.equipos or {}

    if not eq.get("panel_id"):
        e.append("Seleccione un panel.")
    if not eq.get("inversor_id"):
        e.append("Seleccione un inversor.")
    if float(eq.get("sobredimension_dc_ac", 0)) < 1.0:
        e.append("DC/AC inválido (>= 1.0).")

    return len(e) == 0, e
