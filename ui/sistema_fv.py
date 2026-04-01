from __future__ import annotations
from typing import Any, Dict

import streamlit as st

from ui.state_helpers import ensure_dict, merge_defaults


# ==========================================================
# DEFAULTS
# ==========================================================
def _defaults_sistema_fv() -> Dict[str, Any]:
    return {
        "latitud": 15.8,
        "longitud": -87.2,
        "modo_diseno": "auto",
        "usar_zonas": False,
        "sizing_input": {
            "modo": "cobertura",
            "valor": 80.0
        },
        "zonas": [],
    }


# ==========================================================
# STATE
# ==========================================================
def _get_sf(ctx) -> Dict[str, Any]:
    sf = ensure_dict(ctx, "sistema_fv", dict)
    merge_defaults(sf, _defaults_sistema_fv())
    return sf


# ==========================================================
# DIMENSIONAMIENTO
# ==========================================================
def _render_dimensionamiento(sf):

    st.markdown("### Dimensionamiento")

    modo = st.radio(
        "Modo de dimensionamiento",
        ["Automático", "Manual"],
        key="modo_principal"
    )

    # ======================================================
    # AUTOMÁTICO
    # ======================================================
    if modo == "Automático":

        sf["modo_diseno"] = "auto"
        sf["usar_zonas"] = False
        sf["zonas"] = []

        auto_op = st.radio(
            "Método automático",
            ["Cobertura (%)", "Área (m²)", "Potencia (kW)"],
            key="auto_metodo"
        )

        if auto_op == "Cobertura (%)":
            valor = st.number_input("Cobertura (%)", 1.0, 200.0, 80.0)

            sf["modo"] = "cobertura"  # 🔥 FIX
            sf["sizing_input"] = {
                "modo": "cobertura",
                "valor": float(valor)
            }

        elif auto_op == "Área (m²)":
            valor = st.number_input("Área (m²)", 1.0, 10000.0, 100.0)

            sf["modo"] = "area"  # 🔥 FIX
            sf["sizing_input"] = {
                "modo": "area",
                "valor": float(valor)
            }

        elif auto_op == "Potencia (kW)":
            valor = st.number_input("Potencia (kW)", 0.1, 1000.0, 10.0)

            sf["modo"] = "kw_objetivo"  # 🔥 FIX
            sf["sizing_input"] = {
                "modo": "kw_objetivo",
                "valor": float(valor)
            }

    # ======================================================
    # MANUAL
    # ======================================================
    else:

        sf["modo_diseno"] = "manual"

        manual_op = st.radio(
            "Modo manual",
            ["Cantidad de paneles", "Por zonas"],
            key="manual_metodo"
        )

        # --------------------------------------------------
        # MANUAL SIMPLE
        # --------------------------------------------------
        if manual_op == "Cantidad de paneles":

            valor = st.number_input("Paneles", 1, 10000, 30)

            sf["modo"] = "paneles"  # 🔥 FIX
            sf["sizing_input"] = {
                "modo": "paneles",
                "valor": int(valor)
            }

            sf["usar_zonas"] = False
            sf["zonas"] = []

        # --------------------------------------------------
        # MULTIZONA (🔥 CLAVE)
        # --------------------------------------------------
        else:

            sf["usar_zonas"] = True

            sf["modo"] = "multizona"  # 🔥 FIX CRÍTICO
            sf["sizing_input"] = {
                "modo": "multizona"
            }

            # inicialización segura
            if not sf.get("zonas"):
                sf["zonas"] = [{
                    "nombre": "Zona 1",
                    "modo": "Área",
                    "area": 20.0,
                    "n_paneles": None,
                    "azimut": 180.0,
                    "inclinacion": 15.0,
                }]
# ==========================================================
# ZONAS
# ==========================================================
def _render_zonas(sf):

    st.markdown("### Zonas de instalación")

    if st.button("➕ Agregar zona"):
        sf["zonas"].append({
            "nombre": f"Zona {len(sf['zonas']) + 1}",
            "modo": "Área",
            "area": 20.0,
            "n_paneles": None,
            "azimut": 180.0,
            "inclinacion": 15.0,
        })

    nuevas = []

    for i, z in enumerate(sf["zonas"]):

        with st.expander(f"Zona {i+1}", expanded=True):

            z["nombre"] = st.text_input("Nombre", z["nombre"], key=f"n{i}")

            z["modo"] = st.radio(
                "Modo de zona",
                ["Área", "Paneles"],
                index=0 if z.get("modo") == "Área" else 1,
                key=f"m{i}"
            )

            if z["modo"] == "Área":
                z["area"] = st.number_input(
                    "Área (m²)",
                    1.0,
                    10000.0,
                    float(z.get("area") or 20.0),
                    key=f"a{i}"
                )
                z["n_paneles"] = None

            else:
                valor = z.get("n_paneles")
                valor = 10 if valor in [None, 0] else int(valor)

                z["n_paneles"] = st.number_input(
                    "Paneles",
                    1,
                    10000,
                    valor,
                    key=f"p{i}"
                )
                z["area"] = None

            z["inclinacion"] = st.number_input(
                "Inclinación",
                0.0,
                60.0,
                float(z.get("inclinacion") or 15.0),
                key=f"i{i}"
            )

            z["azimut"] = st.number_input(
                "Azimut",
                0.0,
                360.0,
                float(z.get("azimut") or 180.0),
                key=f"az{i}"
            )

            if st.button("Eliminar", key=f"d{i}"):
                continue

            nuevas.append(z)

    sf["zonas"] = nuevas


# ==========================================================
# RENDER
# ==========================================================
def render(ctx):

    st.markdown("## Sistema Fotovoltaico")

    sf = _get_sf(ctx)

    _render_dimensionamiento(sf)

    if sf.get("usar_zonas"):
        _render_zonas(sf)

    ctx.sistema_fv = sf
    # ======================================================
    # 🔥 TRADUCCIÓN SIMPLE (NO TOCAR NADA MÁS)
    # ======================================================

    if sf.get("usar_zonas"):
        sf["modo"] = "multizona"
        sf["valor"] = None

    else:
        sizing = sf.get("sizing_input", {}) or {}
        sf["modo"] = sizing.get("modo")
        sf["valor"] = sizing.get("valor")

    # limpieza
    if sf.get("modo") != "multizona":
        sf["zonas"] = []

# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx):

    sf = _get_sf(ctx)

    errores = []

    if sf.get("usar_zonas"):

        if not sf.get("zonas"):
            errores.append("Debe agregar al menos una zona.")

        for i, z in enumerate(sf["zonas"]):

            if z["modo"] == "Paneles":
                if not z.get("n_paneles") or z["n_paneles"] <= 0:
                    errores.append(f"Zona {i+1}: paneles inválidos")
            else:
                if not z.get("area") or z["area"] <= 0:
                    errores.append(f"Zona {i+1}: área inválida")

    else:

        sizing = sf.get("sizing_input", {})
        valor = sizing.get("valor")

        if valor is None or float(valor) <= 0:
            errores.append("Valor de dimensionamiento inválido.")

    return len(errores) == 0, errores
