from __future__ import annotations
from typing import Any, Dict, List, Tuple
import streamlit as st
from ui.state_helpers import ensure_dict, merge_defaults

# Defaults del sistema FV
def _defaults_sistema_fv() -> Dict[str, Any]:
    return {
        "modo_dimensionado": "auto",
        "n_paneles_manual": 10,
        "inclinacion_deg": 15,
        "azimut_deg": 180,
        "tipo_superficie": "Un plano (suelo/losa/estructura)",
        "azimut_a_deg": 90,
        "azimut_b_deg": 270,
        "reparto_pct_a": 50.0,
        "sombras_pct": 0.0,
        "perdidas_sistema_pct": 15.0,
    }

def _asegurar_dict(ctx, nombre: str) -> Dict[str, Any]:
    return ensure_dict(ctx, nombre, dict)

def _get_sf(ctx) -> Dict[str, Any]:
    sf = _asegurar_dict(ctx, "sistema_fv")
    merge_defaults(sf, _defaults_sistema_fv())
    return sf

# --- Sub-secciones ---
def _render_modo_dimensionado(sf: Dict[str, Any]) -> None:
    st.markdown("#### Dimensionamiento del sistema")
    modo = st.radio(
        "Seleccione modo de dimensionamiento",
        ["Automático (por cobertura)", "Manual (definir cantidad de paneles)"],
        index=0 if sf.get("modo_dimensionado") != "manual" else 1
    )
    sf["modo_dimensionado"] = "manual" if "Manual" in modo else "auto"
    if sf["modo_dimensionado"] == "manual":
        sf["n_paneles_manual"] = st.number_input(
            "Cantidad de paneles",
            min_value=1,
            max_value=1000,
            step=1,
            value=int(sf.get("n_paneles_manual", 10))
        )

def _render_geometria(sf: Dict[str, Any]) -> None:
    st.markdown("#### Geometría del arreglo")
    sf["tipo_superficie"] = st.selectbox(
        "Tipo de superficie",
        ["Un plano (suelo/losa/estructura)", "Techo dos aguas"]
    )
    if sf["tipo_superficie"] == "Techo dos aguas":
        st.caption("Agua A")
        sf["azimut_a_deg"] = st.number_input(
            "Azimut agua A (°)", 0, 360, int(sf.get("azimut_a_deg", 90))
        )
        st.caption("Agua B")
        sf["azimut_b_deg"] = st.number_input(
            "Azimut agua B (°)", 0, 360, int(sf.get("azimut_b_deg", 270))
        )
        sf["reparto_pct_a"] = st.number_input(
            "Reparto paneles agua A (%)", 0.0, 100.0, float(sf.get("reparto_pct_a", 50.0))
        )
    else:
        sf["azimut_deg"] = st.number_input(
            "Azimut (°)", 0, 360, int(sf.get("azimut_deg", 180))
        )
    sf["inclinacion_deg"] = st.number_input(
        "Inclinación (°)", 0, 45, int(sf.get("inclinacion_deg", 15))
    )

def _render_condiciones(sf: Dict[str, Any]) -> None:
    st.markdown("#### Condiciones de instalación")
    sf["sombras_pct"] = st.number_input(
        "Sombras (%)", 0.0, 30.0, float(sf.get("sombras_pct", 0.0))
    )
    sf["perdidas_sistema_pct"] = st.number_input(
        "Pérdidas del sistema (%)", 5.0, 30.0, float(sf.get("perdidas_sistema_pct", 15.0))
    )

# --- API del paso ---
def render(ctx) -> None:
    st.markdown("### Sistema Fotovoltaico")
    sf = _get_sf(ctx)
    _render_modo_dimensionado(sf)
    _render_geometria(sf)
    _render_condiciones(sf)
    ctx.sistema_fv = sf

def validar(ctx) -> Tuple[bool, List[str]]:
    sf = _get_sf(ctx)
    errores: List[str] = []
    if int(sf.get("inclinacion_deg", 0)) < 0:
        errores.append("Inclinación inválida.")
    if sf.get("modo_dimensionado") == "manual" and int(sf.get("n_paneles_manual", 0)) <= 0:
        errores.append("Debe definir una cantidad válida de paneles.")
    return len(errores) == 0, errores
