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
        "latitud": 14.8,
        "longitud": -86.2,

        "sizing_input": {
            "modo": "consumo",
            "valor": 80.0
        },

        "tipo_superficie": "Un plano (suelo/losa/estructura)",

        "azimut_deg": 180,
        "inclinacion_deg": 15,

        "azimut_a_deg": 90,
        "azimut_b_deg": 270,
        "reparto_pct_a": 50.0,

        "sombras_pct": 0.0,
        "perdidas_sistema_pct": 15.0,
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
# GRÁFICOS
# ==========================================================

def _compass_plot(azimut: float):

    fig, ax = plt.subplots(figsize=(2, 2))

    circle = plt.Circle((0, 0), 1, fill=False, linewidth=2)
    ax.add_patch(circle)

    ax.text(0, 1.1, "N", ha="center")
    ax.text(1.1, 0, "E", va="center")
    ax.text(0, -1.1, "S", ha="center")
    ax.text(-1.1, 0, "O", va="center")

    rad = np.deg2rad(90 - azimut)

    x = np.cos(rad)
    y = np.sin(rad)

    ax.arrow(0, 0, x, y, head_width=0.08, head_length=0.12)

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect("equal")
    ax.axis("off")

    return fig


def _roof_plot(tipo, az_a, az_b=None):

    fig, ax = plt.subplots(figsize=(3, 2))

    if tipo == "Un plano (suelo/losa/estructura)":

        ax.plot([0, 4], [0, 0], linewidth=4)
        ax.arrow(2, 0, 0.8, 0, head_width=0.2)

    else:

        ax.plot([0, 2], [0, 1], linewidth=3)
        ax.plot([2, 4], [1, 0], linewidth=3)

        ax.arrow(1, 0.5, 0.7, 0, head_width=0.15)
        ax.arrow(3, 0.5, -0.7, 0, head_width=0.15)

    ax.axis("off")
    return fig


# ==========================================================
# UI — DIMENSIONAMIENTO
# ==========================================================

def _render_modo_dimensionado(sf: Dict[str, Any]):

    st.markdown("### Dimensionamiento del sistema")

    modo = st.radio(
        "¿Cómo deseas dimensionar el sistema?",
        [
            "Cobertura energética",
            "Espacio físico disponible",
            "Potencia objetivo",
            "Manual (definir cantidad de paneles)",
        ],
        index=0
    )

    if "Cobertura" in modo:

        valor = st.slider(
            "Cobertura del consumo (%)",
            min_value=10,
            max_value=150,
            value=int(sf["sizing_input"]["valor"]),
            step=5
        )

        st.caption(f"Valor seleccionado: {valor}%")

        sf["sizing_input"] = {"modo": "consumo", "valor": float(valor)}

    elif "Espacio" in modo:

        valor = st.number_input(
            "Área disponible (m²)",
            min_value=1.0,
            max_value=10000.0,
            value=20.0
        )

        sf["sizing_input"] = {"modo": "area", "valor": float(valor)}

    elif "Potencia" in modo:

        valor = st.number_input(
            "Potencia objetivo (kW)",
            min_value=0.1,
            max_value=1000.0,
            value=5.0
        )

        sf["sizing_input"] = {"modo": "potencia", "valor": float(valor)}

    else:

        valor = st.number_input(
            "Cantidad de paneles",
            min_value=1,
            max_value=10000,
            value=10
        )

        sf["sizing_input"] = {"modo": "manual", "valor": int(valor)}


# ==========================================================
# UI — GEOMETRÍA
# ==========================================================
def _render_geometria(sf: Dict[str, Any]):

    st.markdown("### Geometría del sistema")

    if "zonas" not in sf:
        sf["zonas"] = []

    # ==========================================
    # BOTÓN AGREGAR ZONA
    # ==========================================
    if st.button("➕ Agregar zona"):
        sf["zonas"].append({
            "nombre": f"Zona {len(sf['zonas']) + 1}",
            "area": 20.0,
            "azimut": 180.0,
            "inclinacion": 15.0,
        })

    # ==========================================
    # EDITAR ZONAS
    # ==========================================
    zonas_validas = []

    for i, z in enumerate(sf["zonas"]):

        with st.expander(f"Zona {i+1}", expanded=True):

            z["nombre"] = st.text_input(
                "Nombre",
                value=z.get("nombre", f"Zona {i+1}"),
                key=f"nombre_{i}"
            )

            z["area"] = st.number_input(
                "Área (m²)",
                min_value=1.0,
                max_value=10000.0,
                value=float(z.get("area", 20.0)),
                key=f"area_{i}"
            )

            z["inclinacion"] = st.number_input(
                "Inclinación (°)",
                min_value=0.0,
                max_value=60.0,
                value=float(z.get("inclinacion", 15.0)),
                key=f"inc_{i}"
            )

            z["azimut"] = st.number_input(
                "Azimut (°)",
                min_value=0.0,
                max_value=360.0,
                value=float(z.get("azimut", 180.0)),
                key=f"az_{i}"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.pyplot(_compass_plot(z["azimut"]))

            with col2:
                st.pyplot(_roof_plot("Un plano", z["azimut"]))

            # botón eliminar
            if st.button(f"❌ Eliminar zona {i+1}", key=f"del_{i}"):
                continue

            zonas_validas.append(z)

    sf["zonas"] = zonas_validas

# ==========================================================
# UI — CONDICIONES
# ==========================================================

def _render_condiciones(sf: Dict[str, Any]):

    st.markdown("### Condiciones")

    sf["sombras_pct"] = st.number_input(
        "Sombras (%)", 0.0, 30.0, float(sf["sombras_pct"])
    )

    sf["perdidas_sistema_pct"] = st.number_input(
        "Pérdidas (%)", 5.0, 30.0, float(sf["perdidas_sistema_pct"])
    )


# ==========================================================
# RENDER
# ==========================================================

def render(ctx):

    st.markdown("## Sistema Fotovoltaico")

    sf = _get_sf(ctx)

    sf["modo_simulacion"] = "8760"

    st.info("Modo de simulación: Ingeniería (8760 horario)")

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

    entrada = sf.get("sizing_input", {})

    if entrada.get("modo") == "manual":
        if int(entrada.get("valor", 0)) <= 0:
            errores.append("Cantidad de paneles inválida.")

    if float(sf.get("inclinacion_deg", 0)) < 0:
        errores.append("Inclinación inválida.")

    return len(errores) == 0, errores
