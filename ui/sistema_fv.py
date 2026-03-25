# ==========================================================
# UI — SISTEMA FV (LIMPIO + UX PRO)
# ==========================================================

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
        "latitud": 15.8,
        "longitud": -87.2,

        "modo_diseno": "manual",

        "sizing_input": {
            "modo": "consumo",
            "valor": 80.0
        },

        "zonas": [],
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

    ax.arrow(0, 0, np.cos(rad), np.sin(rad), head_width=0.08)

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect("equal")
    ax.axis("off")

    return fig


# ==========================================================
# MODO DE DISEÑO
# ==========================================================

def _render_selector_modo(sf):

    st.markdown("### Modo de diseño")

    modo = st.radio(
        "¿Cómo deseas definir el sistema?",
        [
            "Definir tamaño del sistema",
            "Definir por zonas (techos/superficies)"
        ],
        index=0 if sf["modo_diseno"] == "manual" else 1
    )

    if "zonas" in modo:
        sf["modo_diseno"] = "zonas"
    else:
        sf["modo_diseno"] = "manual"


# ==========================================================
# DIMENSIONAMIENTO PRO (SIN SLIDER)
# ==========================================================

def _render_modo_dimensionado(sf):

    st.markdown("### Dimensionamiento")

    metodo = st.radio(
        "Método",
        [
            "Cobertura energética",
            "Espacio físico disponible",
            "Potencia objetivo",
            "Manual (paneles)"
        ],
        key="metodo_dimensionado"
    )

    # ----------------------------------
    # BOTÓN INTELIGENTE
    # ----------------------------------
    if st.button("⚡ Aplicar valores recomendados"):

        if metodo == "Cobertura energética":
            sf["sizing_input"] = {"modo": "consumo", "valor": 80.0}

        elif metodo == "Espacio físico disponible":
            sf["sizing_input"] = {"modo": "area", "valor": 100.0}

        elif metodo == "Potencia objetivo":
            sf["sizing_input"] = {"modo": "potencia", "valor": 10.0}

        elif metodo == "Manual (paneles)":
            sf["sizing_input"] = {"modo": "manual", "valor": 30}

    # ----------------------------------
    # MOSTRAR RESULTADO
    # ----------------------------------
    modo_actual = sf["sizing_input"]["modo"]
    valor = sf["sizing_input"]["valor"]

    if modo_actual == "consumo":
        st.success(f"Cobertura configurada: {valor} %")

    elif modo_actual == "area":
        st.success(f"Área configurada: {valor} m²")

    elif modo_actual == "potencia":
        st.success(f"Potencia configurada: {valor} kW")

    elif modo_actual == "manual":
        st.success(f"Paneles configurados: {valor}")


# ==========================================================
# MULTI-ZONA
# ==========================================================

def _render_zonas(sf):

    st.markdown("### Zonas de instalación")

    if st.button("➕ Agregar zona"):
        sf["zonas"].append({
            "nombre": f"Zona {len(sf['zonas']) + 1}",
            "area": 20.0,
            "azimut": 180.0,
            "inclinacion": 15.0,
        })

    nuevas = []

    for i, z in enumerate(sf["zonas"]):

        with st.expander(f"Zona {i+1}", expanded=True):

            z["nombre"] = st.text_input("Nombre", z["nombre"], key=f"n{i}")
            z["area"] = st.number_input("Área", 1.0, 10000.0, z["area"], key=f"a{i}")
            z["inclinacion"] = st.number_input("Inclinación", 0.0, 60.0, z["inclinacion"], key=f"i{i}")
            z["azimut"] = st.number_input("Azimut", 0.0, 360.0, z["azimut"], key=f"az{i}")

            st.pyplot(_compass_plot(z["azimut"]))

            if st.button("Eliminar", key=f"d{i}"):
                continue

            nuevas.append(z)

    sf["zonas"] = nuevas


# ==========================================================
# RENDER PRINCIPAL
# ==========================================================

def render(ctx):

    st.markdown("## Sistema Fotovoltaico")

    sf = _get_sf(ctx)

    _render_selector_modo(sf)

    if sf["modo_diseno"] == "manual":
        _render_modo_dimensionado(sf)
    else:
        _render_zonas(sf)

    ctx.sistema_fv = sf


# ==========================================================
# VALIDACIÓN
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    sf = _get_sf(ctx)

    errores = []

    if sf["modo_diseno"] == "manual":

        if float(sf["sizing_input"].get("valor", 0)) <= 0:
            errores.append("Valor de dimensionamiento inválido.")

    else:

        if not sf.get("zonas"):
            errores.append("Debe definir al menos una zona.")

    return len(errores) == 0, errores
