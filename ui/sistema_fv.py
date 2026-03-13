from __future__ import annotations
from typing import Any, Dict, List, Tuple

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

from ui.state_helpers import ensure_dict, merge_defaults


# ==========================================================
# DEFAULTS
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

        "latitud": 14.8,
        "longitud": -86.2,
    }


# ==========================================================
# HELPERS
# ==========================================================

def _asegurar_dict(ctx, nombre: str) -> Dict[str, Any]:
    return ensure_dict(ctx, nombre, dict)


def _get_sf(ctx) -> Dict[str, Any]:
    sf = _asegurar_dict(ctx, "sistema_fv")
    merge_defaults(sf, _defaults_sistema_fv())
    return sf


# ==========================================================
# DIRECCIÓN CARDINAL
# ==========================================================

def _direccion_cardinal(az: float) -> str:

    dirs = [
        (22.5,"N"),
        (67.5,"NE"),
        (112.5,"E"),
        (157.5,"SE"),
        (202.5,"S"),
        (247.5,"SO"),
        (292.5,"O"),
        (337.5,"NO"),
        (360,"N")
    ]

    for lim, d in dirs:
        if az <= lim:
            return d

    return "N"


# ==========================================================
# BRÚJULA SOLAR
# ==========================================================

def _compass_plot(azimut: float):

    fig, ax = plt.subplots(figsize=(3,3))

    ax.set_xlim(-1,1)
    ax.set_ylim(-1,1)

    circle = plt.Circle((0,0),1,fill=False)
    ax.add_patch(circle)

    ax.text(0,1.1,"N",ha="center")
    ax.text(1.1,0,"E",va="center")
    ax.text(0,-1.15,"S",ha="center")
    ax.text(-1.15,0,"O",va="center")

    rad = np.deg2rad(90-azimut)

    x = np.cos(rad)
    y = np.sin(rad)

    ax.arrow(
        0,0,
        x*0.8,
        y*0.8,
        head_width=0.08,
        head_length=0.1,
        fc="orange",
        ec="orange",
        linewidth=2
    )

    ax.set_aspect("equal")
    ax.axis("off")

    return fig


# ==========================================================
# MODO DIMENSIONADO
# ==========================================================

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


# ==========================================================
# GEOMETRÍA DEL ARREGLO
# ==========================================================

def _render_geometria(sf: Dict[str, Any]) -> None:

    st.markdown("#### Geometría del arreglo")

    # ----------------------------------
    # UBICACIÓN
    # ----------------------------------

    st.markdown("##### Ubicación del proyecto")

    col1, col2 = st.columns(2)

    with col1:

        sf["latitud"] = st.number_input(
            "Latitud",
            value=float(sf.get("latitud", 14.8)),
            format="%.6f"
        )

    with col2:

        sf["longitud"] = st.number_input(
            "Longitud",
            value=float(sf.get("longitud", -86.2)),
            format="%.6f"
        )

    # ----------------------------------
    # SUPERFICIE
    # ----------------------------------

    sf["tipo_superficie"] = st.selectbox(
        "Tipo de superficie",
        ["Un plano (suelo/losa/estructura)", "Techo dos aguas"]
    )

    # ----------------------------------
    # BOTONES ORIENTACIÓN
    # ----------------------------------

    st.caption("Orientación rápida")

    col1,col2,col3,col4 = st.columns(4)

    if col1.button("N"):
        sf["azimut_deg"] = 0

    if col2.button("E"):
        sf["azimut_deg"] = 90

    if col3.button("S"):
        sf["azimut_deg"] = 180

    if col4.button("O"):
        sf["azimut_deg"] = 270
    st.success("UI solar cargada")

    # ----------------------------------
    # CONFIGURACIÓN
    # ----------------------------------

    if sf["tipo_superficie"] == "Techo dos aguas":

        st.caption("Agua A")

        sf["azimut_a_deg"] = st.number_input(
            "Azimut agua A (°)",
            0,
            360,
            int(sf.get("azimut_a_deg", 90))
        )

        st.caption("Agua B")

        sf["azimut_b_deg"] = st.number_input(
            "Azimut agua B (°)",
            0,
            360,
            int(sf.get("azimut_b_deg", 270))
        )

        sf["reparto_pct_a"] = st.number_input(
            "Reparto paneles agua A (%)",
            0.0,
            100.0,
            float(sf.get("reparto_pct_a", 50.0))
        )

        az = sf["azimut_a_deg"]

    else:

        sf["azimut_deg"] = st.number_input(
            "Azimut (°)",
            0,
            360,
            int(sf.get("azimut_deg", 180))
        )

        az = sf["azimut_deg"]

    # ----------------------------------
    # BRÚJULA
    # ----------------------------------

    direccion = _direccion_cardinal(az)

    st.caption(f"Dirección: **{direccion}**")

    fig = _compass_plot(az)

    st.pyplot(fig)

    # ----------------------------------
    # INCLINACIÓN
    # ----------------------------------

    sf["inclinacion_deg"] = st.number_input(
        "Inclinación (°)",
        0,
        45,
        int(sf.get("inclinacion_deg", 15))
    )


# ==========================================================
# CONDICIONES
# ==========================================================

def _render_condiciones(sf: Dict[str, Any]) -> None:

    st.markdown("#### Condiciones de instalación")

    sf["sombras_pct"] = st.number_input(
        "Sombras (%)",
        0.0,
        30.0,
        float(sf.get("sombras_pct", 0.0))
    )

    sf["perdidas_sistema_pct"] = st.number_input(
        "Pérdidas del sistema (%)",
        5.0,
        30.0,
        float(sf.get("perdidas_sistema_pct", 15.0))
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

    ctx.sistema_fv = sf


# ==========================================================
# VALIDACIÓN
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    sf = _get_sf(ctx)

    errores: List[str] = []

    if int(sf.get("inclinacion_deg", 0)) < 0:
        errores.append("Inclinación inválida.")

    if sf.get("modo_dimensionado") == "manual" and int(sf.get("n_paneles_manual", 0)) <= 0:
        errores.append("Debe definir una cantidad válida de paneles.")

    return len(errores) == 0, errores
