from __future__ import annotations
from typing import List, Tuple, Dict, Any
import streamlit as st

from electrical.catalogos import catalogo_paneles, catalogo_inversores
from ui.state_helpers import ensure_dict, merge_defaults


# ==========================================================
# DEFAULTS
# ==========================================================

def _defaults(ctx) -> None:
    eq = ensure_dict(ctx, "equipos", dict)
    merge_defaults(eq, {
        "panel_id": None,
        "inversor_id": None,
        "sobredimension_dc_ac": 1.20,
        "tension_sistema": "2F+N_120/240",
        "strings_config": None,
    })
    ctx.equipos = eq


# ==========================================================
# HELPERS
# ==========================================================

def _safe_index(opciones: List[str], valor_actual: str | None) -> int:
    return opciones.index(valor_actual) if valor_actual in opciones else 0


# ==========================================================
# MAPEO DE CATÁLOGOS
# ==========================================================

def _panel_to_ui(pid: str, p: Dict[str, Any]) -> Dict[str, Any]:
    stc = p.get("stc", p)
    return {
        "id": pid,
        "marca": p.get("marca", "N/D"),
        "modelo": p.get("nombre", "Panel"),
        "pmax_w": float(stc.get("pmax_w", 0)),
        "vmp_v": float(stc.get("vmp_v", 0)),
        "voc_v": float(stc.get("voc_v", 0)),
        "imp_a": float(stc.get("imp_a", 0)),
        "isc_a": float(stc.get("isc_a", 0)),
    }


def _inv_to_ui(iid: str, inv: Dict[str, Any]) -> Dict[str, Any]:
    dc = inv.get("entrada_dc", inv)
    ac = inv.get("salida_ac", inv)
    return {
        "id": iid,
        "marca": inv.get("marca", "N/D"),
        "modelo": inv.get("nombre", "Inversor"),
        "kw_ac": float(ac.get("kw_ac", ac.get("pac_w", 0))),
        "n_mppt": int(dc.get("n_mppt", 1)),
        "mppt_min_v": float(dc.get("mppt_min_v", 0)),
        "mppt_max_v": float(dc.get("mppt_max_v", 0)),
        "vmax_dc_v": float(dc.get("vdc_max_v", 0)),
    }


def _load_paneles():
    return [_panel_to_ui(p["id"], p) for p in catalogo_paneles()]


def _load_inversores():
    return [_inv_to_ui(i["id"], i) for i in catalogo_inversores()]


def _map_por_id(items):
    return {i["id"]: i for i in items}


# ==========================================================
# UI
# ==========================================================

def _ui_select_panel(eq, panel_ids, panel_map):
    eq["panel_id"] = st.selectbox(
        "Panel FV",
        panel_ids,
        index=_safe_index(panel_ids, eq.get("panel_id")),
        format_func=lambda pid:
        f'{panel_map[pid]["marca"]} {panel_map[pid]["modelo"]} ({panel_map[pid]["pmax_w"]:.0f} W)'
    )


def _ui_select_inversor(eq, inv_ids, inv_map):
    eq["inversor_id"] = st.selectbox(
        "Inversor",
        inv_ids,
        index=_safe_index(inv_ids, eq.get("inversor_id")),
        format_func=lambda iid:
        f'{inv_map[iid]["marca"]} {inv_map[iid]["modelo"]} ({inv_map[iid]["kw_ac"]:.1f} kW)'
    )


def _ui_criterios(eq):
    st.markdown("### Criterios")

    col1, col2 = st.columns(2)

    with col1:
        eq["sobredimension_dc_ac"] = st.number_input(
            "DC/AC",
            1.1, 1.5,
            float(eq.get("sobredimension_dc_ac", 1.2)),
            step=0.05
        )

    with col2:
        eq["tension_sistema"] = st.selectbox(
            "Tensión",
            ["2F+N_120/240", "3F+N_120/208"]
        )


def _ui_resumen(eq, panel_map, inv_map):
    st.markdown("### Resumen")

    if not eq["panel_id"] or not eq["inversor_id"]:
        return

    p = panel_map[eq["panel_id"]]
    i = inv_map[eq["inversor_id"]]

    st.write(f"Panel: {p['marca']} {p['modelo']} ({p['pmax_w']} W)")
    st.write(f"Inversor: {i['marca']} {i['modelo']} ({i['kw_ac']} kW)")


# ==========================================================
# 🔥 CONFIGURACIÓN DE STRINGS (NUEVO)
# ==========================================================

def _ui_configuracion_arreglo(ctx, eq, panel_map, inv_map):

    st.markdown("### ⚡ Configuración del arreglo FV")

    sf = getattr(ctx, "sistema_fv", {})
    entrada = sf.get("sizing_input", {})

    if not eq.get("panel_id") or not eq.get("inversor_id"):
        st.info("Selecciona panel e inversor primero")
        return

    total_paneles = int(entrada.get("valor", 0))
    modo = entrada.get("modo")

    if modo != "manual":
        st.success("Configuración automática (se generará en backend)")
        eq["strings_config"] = None
        return

    col1, col2 = st.columns(2)

    with col1:
        paneles_por_string = st.number_input("Paneles por string", 1, 30, 10)

    with col2:
        n_strings = st.number_input("Número de strings", 1, 50, 1)

    total_calc = paneles_por_string * n_strings

    st.write(f"Total configurado: {total_calc} paneles")

    if total_calc != total_paneles:
        st.warning("No coincide con el total de paneles")

    eq["strings_config"] = {
        "paneles_por_string": int(paneles_por_string),
        "n_strings": int(n_strings),
    }


# ==========================================================
# RENDER
# ==========================================================

def render(ctx):

    _defaults(ctx)
    eq = ctx.equipos

    st.markdown("## Selección de equipos")

    paneles = _load_paneles()
    inversores = _load_inversores()

    panel_map = _map_por_id(paneles)
    inv_map = _map_por_id(inversores)

    panel_ids = list(panel_map.keys())
    inv_ids = list(inv_map.keys())

    col1, col2 = st.columns(2)

    with col1:
        _ui_select_panel(eq, panel_ids, panel_map)

    with col2:
        _ui_select_inversor(eq, inv_ids, inv_map)

    _ui_criterios(eq)
    _ui_resumen(eq, panel_map, inv_map)

    # 🔥 NUEVO BLOQUE
    _ui_configuracion_arreglo(ctx, eq, panel_map, inv_map)

    ctx.equipos = eq


# ==========================================================
# VALIDACIÓN
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    errores = []
    eq = getattr(ctx, "equipos", {})

    if not eq.get("panel_id"):
        errores.append("Seleccione panel")

    if not eq.get("inversor_id"):
        errores.append("Seleccione inversor")

    return len(errores) == 0, errores
