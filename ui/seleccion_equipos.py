# ui/seleccion_equipos.py
from __future__ import annotations
from typing import List, Tuple
import streamlit as st

from electrical.catalogos import catalogo_paneles, catalogo_inversores


def _defaults(ctx) -> None:
    if not ctx.equipos:
        ctx.equipos = {
            "panel_id": None,
            "inversor_id": None,
            "sobredimension_dc_ac": 1.20,
            "tension_sistema": "1F_240V",
        }


def _safe_index(opciones: List[str], valor_actual: str | None) -> int:
    if not opciones:
        return 0
    if valor_actual in opciones:
        return opciones.index(valor_actual)
    return 0


def render(ctx) -> None:
    _defaults(ctx)
    eq = ctx.equipos

    st.markdown("### Selección de equipos")

    # ===== Cargar catálogos (API pública electrical) =====
    paneles = catalogo_paneles()
    inversores = catalogo_inversores()

    if not paneles:
        st.error("Catálogo de paneles vacío. Revise electrical/catalogos.py.")
        return
    if not inversores:
        st.error("Catálogo de inversores vacío. Revise electrical/catalogos.py.")
        return

    panel_map = {p["id"]: p for p in paneles}
    inv_map = {i["id"]: i for i in inversores}

    panel_ids = list(panel_map.keys())
    inv_ids = list(inv_map.keys())

    col1, col2 = st.columns(2)

    with col1:
        eq["panel_id"] = st.selectbox(
            "Panel FV",
            options=panel_ids,
            index=_safe_index(panel_ids, eq.get("panel_id")),
            format_func=lambda pid: f'{panel_map[pid]["marca"]} {panel_map[pid]["modelo"]} ({panel_map[pid]["pmax_w"]} W)',
        )

    with col2:
        eq["inversor_id"] = st.selectbox(
            "Inversor",
            options=inv_ids,
            index=_safe_index(inv_ids, eq.get("inversor_id")),
            format_func=lambda iid: f'{inv_map[iid]["marca"]} {inv_map[iid]["modelo"]} ({inv_map[iid]["pac_kw"]} kW)',
        )

    st.markdown("#### Criterios")
    a, b = st.columns(2)

    with a:
        eq["sobredimension_dc_ac"] = st.number_input(
            "Objetivo DC/AC",
            min_value=1.0,
            max_value=1.6,
            step=0.05,
            value=float(eq.get("sobredimension_dc_ac", 1.20)),
        )

    with b:
        opciones_v = ["1F_240V", "3F_208Y120V", "3F_480Y277V"]
        eq["tension_sistema"] = st.selectbox(
            "Tensión del sistema",
            options=opciones_v,
            index=_safe_index(opciones_v, eq.get("tension_sistema", "1F_240V")),
        )

    # ===== Preview técnico rápido =====
    st.markdown("#### Resumen técnico")
    p = panel_map[eq["panel_id"]]
    inv = inv_map[eq["inversor_id"]]

    st.write(
        f"**Panel:** {p['marca']} {p['modelo']} — "
        f"Pmax {p['pmax_w']:.0f} W | Voc {p['voc_v']:.1f} V | Vmp {p['vmp_v']:.1f} V"
    )
    st.write(
        f"**Inversor:** {inv['marca']} {inv['modelo']} — "
        f"AC {inv['pac_kw']:.1f} kW | MPPT {inv['mppt_min_v']:.0f}-{inv['mppt_max_v']:.0f} V | "
        f"Vdc max {inv['vmax_dc_v']:.0f} V | MPPTs {inv['n_mppt']}"
    )

    ctx.equipos = eq


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []
    eq = ctx.equipos or {}

    if not eq.get("panel_id"):
        errores.append("Seleccione un panel.")
    if not eq.get("inversor_id"):
        errores.append("Seleccione un inversor.")
    if float(eq.get("sobredimension_dc_ac", 0)) < 1.0:
        errores.append("DC/AC inválido (>= 1.0).")

    return (len(errores) == 0), errores
