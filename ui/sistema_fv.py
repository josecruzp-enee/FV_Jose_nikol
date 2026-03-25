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

        "modo_dimensionado": "auto",
        "n_paneles_manual": 10,

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
# BRÚJULA DE ORIENTACIÓN
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

    ax.arrow(
        0,
        0,
        x,
        y,
        head_width=0.08,
        head_length=0.12,
        fc="orange",
        ec="orange",
        linewidth=2
    )

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)

    ax.set_aspect("equal")
    ax.axis("off")

    return fig


# ==========================================================
# DIBUJO DEL TECHO
# ==========================================================

def _roof_plot(tipo, az_a, az_b=None):

    fig, ax = plt.subplots(figsize=(3, 2))

    if tipo == "Un plano (suelo/losa/estructura)":

        ax.plot([0, 4], [0, 0], linewidth=4)

        ax.arrow(
            2,
            0,
            0.8,
            0,
            head_width=0.2,
            head_length=0.2,
            fc="orange",
            ec="orange"
        )

        ax.text(2, -0.5, "Paneles")

    elif tipo == "Techo dos aguas":

        ax.plot([0, 2], [0, 1], linewidth=3)
        ax.plot([2, 4], [1, 0], linewidth=3)

        ax.arrow(1, 0.5, 0.7, 0, head_width=0.15, fc="orange")
        ax.arrow(3, 0.5, -0.7, 0, head_width=0.15, fc="orange")

        ax.text(1, 0.9, "Agua A")
        ax.text(3, 0.9, "Agua B")

    ax.set_xlim(-0.5, 4.5)
    ax.set_ylim(-1, 2)

    ax.axis("off")

    return fig


# ==========================================================
# SUBSECCIONES UI
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

# -----------------------------
# NORMALIZAR VALOR INTERNO
# -----------------------------
if "Cobertura" in modo:
    sf["modo_dimensionado"] = "consumo"

elif "Espacio" in modo:
    sf["modo_dimensionado"] = "area"

elif "Potencia" in modo:
    sf["modo_dimensionado"] = "potencia"

else:
    sf["modo_dimensionado"] = "manual"

# =============================
# MODO COBERTURA
# =============================
if sf["modo_dimensionado"] == "consumo":

    sf["cobertura_pct"] = st.slider(
        "Cobertura del consumo (%)",
        50.0,
        120.0,
        float(sf.get("cobertura_pct", 80.0))
    )

    st.info(
        f"Sistema dimensionado al {sf['cobertura_pct']:.0f}% del consumo anual"
    )

# =============================
# MODO ÁREA
# =============================
elif sf["modo_dimensionado"] == "area":

    sf["area_disponible_m2"] = st.number_input(
        "Área disponible (m²)",
        min_value=1.0,
        value=float(sf.get("area_disponible_m2", 50.0))
    )

    sf["factor_ocupacion"] = st.slider(
        "Factor de ocupación",
        0.5,
        0.9,
        float(sf.get("factor_ocupacion", 0.75))
    )

    area_util = sf["area_disponible_m2"] * sf["factor_ocupacion"]
    kwp_area = area_util / 5

    st.info(f"Capacidad máxima estimada: {kwp_area:.2f} kWp")

# =============================
# MODO POTENCIA
# =============================
elif sf["modo_dimensionado"] == "potencia":

    sf["kwp_objetivo"] = st.number_input(
        "Potencia objetivo (kWp)",
        min_value=0.5,
        max_value=1000.0,
        value=float(sf.get("kwp_objetivo", 5.0))
    )

    st.info(
        f"Sistema definido a {sf['kwp_objetivo']:.2f} kWp DC"
    )

# =============================
# MODO MANUAL
# =============================
elif sf["modo_dimensionado"] == "manual":

    sf["n_paneles_manual"] = st.number_input(
        "Cantidad de paneles",
        min_value=1,
        max_value=2000,
        value=int(sf.get("n_paneles_manual", 10))
    )


# ==========================================================

def _render_geometria(sf: Dict[str, Any]):

    st.markdown("### Geometría del arreglo")

    st.markdown("#### Ubicación del proyecto")

    c1, c2 = st.columns(2)

    with c1:
        sf["latitud"] = st.number_input(
            "Latitud",
            value=float(sf.get("latitud", 14.8)),
            format="%.6f"
        )

    with c2:
        sf["longitud"] = st.number_input(
            "Longitud",
            value=float(sf.get("longitud", -86.2)),
            format="%.6f"
        )

    sf["tipo_superficie"] = st.selectbox(
        "Tipo de superficie",
        [
            "Un plano (suelo/losa/estructura)",
            "Techo dos aguas"
        ]
    )

    if sf["tipo_superficie"] == "Techo dos aguas":

        st.markdown("##### Agua A")

        sf["azimut_a_deg"] = st.number_input(
            "Azimut agua A (°)",
            0,
            360,
            int(sf.get("azimut_a_deg", 90))
        )

        st.markdown("##### Agua B")

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

        fig = _roof_plot(
            sf["tipo_superficie"],
            sf["azimut_a_deg"],
            sf["azimut_b_deg"]
        )

        st.pyplot(fig)

    else:

        sf["azimut_deg"] = st.number_input(
            "Azimut (°)",
            0,
            360,
            int(sf.get("azimut_deg", 180))
        )

        fig = _compass_plot(sf["azimut_deg"])

        st.pyplot(fig)

    sf["inclinacion_deg"] = st.number_input(
        "Inclinación (°)",
        0,
        45,
        int(sf.get("inclinacion_deg", 15))
    )


# ==========================================================

def _render_condiciones(sf: Dict[str, Any]):

    st.markdown("### Condiciones de instalación")

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

def render(ctx):

    st.markdown("## Sistema Fotovoltaico")

    sf = _get_sf(ctx)

    # --------------------------------------------------
    # MODO FIJO (8760)
    # --------------------------------------------------

    sf["modo_simulacion"] = "8760"

    st.info("Modo de simulación: Ingeniería (8760 horario)")

    # --------------------------------------------------
    # RESTO UI
    # --------------------------------------------------

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

    if sf.get("modo_dimensionado") == "manual":

        if int(sf.get("n_paneles_manual", 0)) <= 0:

            errores.append("Cantidad de paneles inválida.")

    if int(sf.get("inclinacion_deg", 0)) < 0:

        errores.append("Inclinación inválida.")

    return len(errores) == 0, errores
