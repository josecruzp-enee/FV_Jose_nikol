# ==========================================================
# UI — SISTEMA FV (MULTIZONA PROFESIONAL)
# ==========================================================

from __future__ import annotations
from typing import Any, Dict, List, Tuple

import streamlit as st

from ui.state_helpers import ensure_dict, merge_defaults

# 🔥 IMPORTANTE (ajusta ruta si es necesario)
from electrical.paneles.entrada_panel import ZonaFV


# ==========================================================
# DEFAULTS
# ==========================================================

def _defaults_sistema_fv() -> Dict[str, Any]:
    return {
        "latitud": 15.8,
        "longitud": -87.2,
        "modo_diseno": "auto",
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


# 🔥 CONVERSIÓN SIMPLE ÁREA → PANELES
def _area_a_paneles(area_m2: float, panel_area: float = 2.0) -> int:
    return max(1, int(area_m2 / panel_area))


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

        auto_op = st.radio(
            "Método automático",
            ["Cobertura (%)", "Área (m²)", "Potencia (kW)"],
            key="auto_metodo"
        )

        if auto_op == "Cobertura (%)":
            valor = st.number_input("Cobertura", 0.0, 200.0, 80.0)
            sf["sizing_input"] = {"modo": "consumo", "valor": float(valor)}

        elif auto_op == "Área (m²)":
            valor = st.number_input("Área", 1.0, 10000.0, 100.0)
            sf["sizing_input"] = {"modo": "area", "valor": float(valor)}

        elif auto_op == "Potencia (kW)":
            valor = st.number_input("Potencia", 0.1, 1000.0, 10.0)
            sf["sizing_input"] = {"modo": "kw_objetivo", "valor": float(valor)}

    # ======================================================
    # MANUAL
    # ======================================================
    else:

        manual_op = st.radio(
            "Modo manual",
            ["Cantidad de paneles", "Por zonas"],
            key="manual_metodo"
        )

        if manual_op == "Cantidad de paneles":
            valor = st.number_input("Paneles", 1, 10000, 30)
            sf["sizing_input"] = {"modo": "manual", "valor": int(valor)}
            sf["modo_diseno"] = "manual"

        elif manual_op == "Por zonas":
            sf["modo_diseno"] = "zonas"
            sf["sizing_input"] = {}


# ==========================================================
# ZONAS (🔥 PRO)
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

            # 🔥 MODO DE ZONA
            z["modo"] = st.radio(
                "Modo de zona",
                ["Área", "Paneles"],
                key=f"m{i}"
            )

            # ------------------------------------------------
            # INPUTS DINÁMICOS
            # ------------------------------------------------
            if z["modo"] == "Área":
                z["area"] = st.number_input(
                    "Área (m²)", 1.0, 10000.0, z.get("area", 20.0), key=f"a{i}"
                )
                z["n_paneles"] = None

            else:
                z["n_paneles"] = st.number_input(
                    "Paneles", 1, 10000, z.get("n_paneles", 10), key=f"p{i}"
                )
                z["area"] = None

            z["inclinacion"] = st.number_input(
                "Inclinación", 0.0, 60.0, z["inclinacion"], key=f"i{i}"
            )

            z["azimut"] = st.number_input(
                "Azimut", 0.0, 360.0, z["azimut"], key=f"az{i}"
            )

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

    _render_dimensionamiento(sf)

    if sf["modo_diseno"] == "zonas":
        _render_zonas(sf)

    ctx.sistema_fv = sf


# ==========================================================
# VALIDACIÓN
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    sf = _get_sf(ctx)

    errores = []

    if sf["modo_diseno"] == "zonas":

        if not sf.get("zonas"):
            errores.append("Debe definir al menos una zona.")

        else:
            for i, z in enumerate(sf["zonas"]):

                if z["modo"] == "Paneles":
                    if not z.get("n_paneles") or z["n_paneles"] <= 0:
                        errores.append(f"Zona {i+1}: paneles inválidos")

                else:
                    if not z.get("area") or z["area"] <= 0:
                        errores.append(f"Zona {i+1}: área inválida")

    else:

        if float(sf["sizing_input"].get("valor", 0)) <= 0:
            errores.append("Valor de dimensionamiento inválido.")

    return len(errores) == 0, errores


# ==========================================================
# 🔥 ADAPTADOR UI → DOMINIO
# ==========================================================

def construir_entrada_paneles(sf, panel, inversor, n_inversores, t_min, t_oper):

    # ------------------------------------------------------
    # MODO
    # ------------------------------------------------------
    if sf["modo_diseno"] == "zonas":
        modo = "multizona"
    else:
        modo = sf["sizing_input"]["modo"]

    # ------------------------------------------------------
    # ZONAS
    # ------------------------------------------------------
    zonas_dom = None

    if modo == "multizona":

        zonas_dom = []

        for z in sf["zonas"]:

            if z["modo"] == "Paneles":
                n_paneles = z["n_paneles"]
            else:
                n_paneles = _area_a_paneles(z["area"])

            zonas_dom.append(
                ZonaFV(n_paneles=int(n_paneles))
            )

    # ------------------------------------------------------
    # MANUAL GLOBAL
    # ------------------------------------------------------
    n_paneles_total = None

    if modo == "manual":
        n_paneles_total = int(sf["sizing_input"]["valor"])

    # ------------------------------------------------------
    # CONSTRUIR ENTRADA
    # ------------------------------------------------------
    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo=modo,
        n_paneles_total=n_paneles_total,
        n_inversores=n_inversores,
        zonas=zonas_dom,
        t_min_c=t_min,
        t_oper_c=t_oper,
    )
