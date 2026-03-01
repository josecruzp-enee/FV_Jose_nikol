# ui/sistema_fv.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import streamlit as st
from ui.state_helpers import ensure_dict, merge_defaults


# ==========================================================
# Defaults
# ==========================================================

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


# ==========================================================
# MODO DIMENSIONAMIENTO
# ==========================================================

def _render_modo_dimensionado(sf: Dict[str, Any]) -> None:
    st.markdown("#### Dimensionamiento del sistema")

    modo = st.radio(
        "Seleccione modo de dimensionamiento",
        options=[
            "Automático (por cobertura)",
            "Manual (definir cantidad de paneles)"
        ],
        index=0 if sf.get("modo_dimensionado") != "manual" else 1,
        key="sf_modo_dim",
    )

    sf["modo_dimensionado"] = "manual" if "Manual" in modo else "auto"

    if sf["modo_dimensionado"] == "manual":
        sf["n_paneles_manual"] = st.number_input(
            "Cantidad de paneles a instalar",
            min_value=1,
            max_value=1000,
            step=1,
            value=int(sf.get("n_paneles_manual", 10)),
            key="sf_n_paneles_manual",
        )


# ==========================================================
# GEOMETRÍA
# ==========================================================

def _render_geometria(sf: Dict[str, Any]) -> None:
    st.markdown("#### Geometría del arreglo")

    sf["tipo_superficie"] = st.selectbox(
        "Tipo de superficie",
        options=[
            "Un plano (suelo/losa/estructura)",
            "Techo dos aguas"
        ],
        index=0 if sf.get("tipo_superficie") != "Techo dos aguas" else 1,
    )

    if sf["tipo_superficie"] == "Techo dos aguas":

        st.caption("Agua A")
        sf["azimut_a_deg"] = st.number_input(
            "Azimut agua A (°)",
            min_value=0,
            max_value=360,
            value=int(sf.get("azimut_a_deg", 90)),
            key="sf_azimut_a",
        )

        st.caption("Agua B")
        sf["azimut_b_deg"] = st.number_input(
            "Azimut agua B (°)",
            min_value=0,
            max_value=360,
            value=int(sf.get("azimut_b_deg", 270)),
            key="sf_azimut_b",
        )

        sf["reparto_pct_a"] = st.number_input(
            "Reparto paneles agua A (%)",
            min_value=0.0,
            max_value=100.0,
            step=5.0,
            value=float(sf.get("reparto_pct_a", 50.0)),
            key="sf_reparto_a",
        )

    else:
        sf["azimut_deg"] = st.number_input(
            "Azimut (°)",
            min_value=0,
            max_value=360,
            value=int(sf.get("azimut_deg", 180)),
            key="sf_azimut",
        )

    sf["inclinacion_deg"] = st.number_input(
        "Inclinación (°)",
        min_value=0,
        max_value=45,
        value=int(sf.get("inclinacion_deg", 15)),
        key="sf_inclinacion",
    )


# ==========================================================
# CONDICIONES
# ==========================================================

def _render_condiciones(sf: Dict[str, Any]) -> None:
    st.markdown("#### Condiciones de instalación")

    sf["sombras_pct"] = st.number_input(
        "Sombras (%)",
        min_value=0.0,
        max_value=30.0,
        step=1.0,
        value=float(sf.get("sombras_pct", 0.0)),
        key="sf_sombras",
    )

    sf["perdidas_sistema_pct"] = st.number_input(
        "Pérdidas del sistema (%)",
        min_value=5.0,
        max_value=30.0,
        step=0.5,
        value=float(sf.get("perdidas_sistema_pct", 15.0)),
        key="sf_perdidas",
    )


# ==========================================================
# API DEL PASO
# ==========================================================

def render(ctx) -> None:
    st.markdown("### Sistema Fotovoltaico")

    sf = _get_sf(ctx)

    _render_modo_dimensionado(sf)
    _render_geometria(sf)
    _render_condiciones(sf)

    st.divider()
    st.caption("El perfil mensual HSP es fijo según modelo oficial Honduras.")


def validar(ctx) -> Tuple[bool, List[str]]:
    sf = _get_sf(ctx)
    errs: List[str] = []

    if int(sf.get("inclinacion_deg", 0)) < 0:
        errs.append("Inclinación inválida.")

    if sf.get("modo_dimensionado") == "manual":
        if int(sf.get("n_paneles_manual", 0)) <= 0:
            errs.append("Debe definir una cantidad válida de paneles.")

    return (len(errs) == 0), errs
