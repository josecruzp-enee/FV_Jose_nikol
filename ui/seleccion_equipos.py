# ui/seleccion_equipos.py
from __future__ import annotations

from typing import List, Tuple, Dict, Any
import streamlit as st

from electrical.catalogos_yaml import cargar_paneles_yaml
from electrical.catalogos import catalogo_paneles, catalogo_inversores


def _defaults(ctx) -> None:
    if not getattr(ctx, "equipos", None):
        ctx.equipos = {"panel_id": None, "inversor_id": None, "sobredimension_dc_ac": 1.20, "tension_sistema": "1F_240V"}


def _safe_index(opciones: List[str], valor_actual: str | None) -> int:
    if not opciones:
        return 0
    return opciones.index(valor_actual) if valor_actual in opciones else 0


def _panel_yaml_to_ui(pid: str, p: Dict[str, Any]) -> Dict[str, Any]:
    stc = p.get("stc", p)
    return {
        "id": pid,
        "marca": p.get("marca", "N/D"),
        "modelo": p.get("modelo", p.get("pn", "Panel")),
        "pmax_w": float(stc.get("pmax_w", 0.0)),
        "vmp_v": float(stc.get("vmp_v", 0.0)),
        "voc_v": float(stc.get("voc_v", 0.0)),
        "imp_a": float(stc.get("imp_a", 0.0)),
        "isc_a": float(stc.get("isc_a", 0.0)),
    }


def _try_load_paneles_yaml() -> List[Dict[str, Any]]:
    try:
        data = cargar_paneles_yaml()
        return [_panel_yaml_to_ui(pid, spec) for pid, spec in (data or {}).items()]
    except Exception:
        return []


def _load_paneles() -> List[Dict[str, Any]]:
    py = catalogo_paneles() or []
    yml = _try_load_paneles_yaml()
    return yml if yml else py


def _load_inversores() -> List[Dict[str, Any]]:
    return catalogo_inversores() or []


def _map_por_id(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {it["id"]: it for it in items if isinstance(it, dict) and it.get("id")}


def _validar_catalogos(paneles: List[dict], inversores: List[dict]) -> bool:
    if not paneles:
        st.error("Catálogo de paneles vacío. Revise YAML o electrical/catalogos.py.")
        return False
    if not inversores:
        st.error("Catálogo de inversores vacío. Revise electrical/catalogos.py.")
        return False
    return True


def _ui_select_panel(eq: dict, panel_ids: List[str], panel_map: Dict[str, dict]) -> None:
    eq["panel_id"] = st.selectbox(
        "Panel FV",
        options=panel_ids,
        index=_safe_index(panel_ids, eq.get("panel_id")),
        format_func=lambda pid: f'{panel_map[pid]["marca"]} {panel_map[pid]["modelo"]} ({panel_map[pid]["pmax_w"]} W)',
    )


def _ui_select_inversor(eq: dict, inv_ids: List[str], inv_map: Dict[str, dict]) -> None:
    eq["inversor_id"] = st.selectbox(
        "Inversor",
        options=inv_ids,
        index=_safe_index(inv_ids, eq.get("inversor_id")),
        format_func=lambda iid: f'{inv_map[iid]["marca"]} {inv_map[iid]["modelo"]} ({inv_map[iid]["pac_kw"]} kW)',
    )


def _ui_criterios(eq: dict) -> None:
    st.markdown("#### Criterios")
    a, b = st.columns(2)
    with a:
        eq["sobredimension_dc_ac"] = st.number_input("Objetivo DC/AC", 1.0, 1.6, 0.05, float(eq.get("sobredimension_dc_ac", 1.20)))
    with b:
        ops = ["1F_240V", "3F_208Y120V", "3F_480Y277V"]
        eq["tension_sistema"] = st.selectbox("Tensión del sistema", options=ops, index=_safe_index(ops, eq.get("tension_sistema", "1F_240V")))


def _ui_resumen(eq: dict, panel_map: Dict[str, dict], inv_map: Dict[str, dict]) -> None:
    st.markdown("#### Resumen técnico")
    p = panel_map[eq["panel_id"]]
    inv = inv_map[eq["inversor_id"]]
    st.write(f"**Panel:** {p['marca']} {p['modelo']} — Pmax {p['pmax_w']:.0f} W | Voc {p['voc_v']:.1f} V | Vmp {p['vmp_v']:.1f} V")
    st.write(f"**Inversor:** {inv['marca']} {inv['modelo']} — AC {inv['pac_kw']:.1f} kW | MPPT {inv['mppt_min_v']:.0f}-{inv['mppt_max_v']:.0f} V | Vdc max {inv['vmax_dc_v']:.0f} V | MPPTs {inv['n_mppt']}")


def render(ctx) -> None:
    _defaults(ctx)
    eq = ctx.equipos

    st.markdown("### Selección de equipos")

    paneles = _load_paneles()
    inversores = _load_inversores()
    if not _validar_catalogos(paneles, inversores):
        return

    panel_map = _map_por_id(paneles)
    inv_map = _map_por_id(inversores)
    panel_ids, inv_ids = list(panel_map.keys()), list(inv_map.keys())

    col1, col2 = st.columns(2)
    with col1:
        _ui_select_panel(eq, panel_ids, panel_map)
    with col2:
        _ui_select_inversor(eq, inv_ids, inv_map)

    _ui_criterios(eq)
    _ui_resumen(eq, panel_map, inv_map)
    ctx.equipos = eq


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []
    eq = getattr(ctx, "equipos", None) or {}
    if not eq.get("panel_id"):
        errores.append("Seleccione un panel.")
    if not eq.get("inversor_id"):
        errores.append("Seleccione un inversor.")
    if float(eq.get("sobredimension_dc_ac", 0.0)) < 1.0:
        errores.append("DC/AC inválido (>= 1.0).")
    return (len(errores) == 0), errores
