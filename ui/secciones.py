# ui/secciones.py
from __future__ import annotations
from typing import Dict, Any
import streamlit as st

from electrical.catalogos import PANELES, INVERSORES
from electrical.modelos import ParametrosCableado


def ui_equipos(state: Dict[str, Any]) -> None:
    st.subheader("Equipos")

    panel_nombres = list(PANELES.keys())
    inv_nombres = list(INVERSORES.keys())

    state["panel_sel"] = st.selectbox("Panel", panel_nombres, index=panel_nombres.index(state.get("panel_sel", panel_nombres[0])))
    state["inv_sel"] = st.selectbox("Inversor", inv_nombres, index=inv_nombres.index(state.get("inv_sel", inv_nombres[0])))
    state["dos_aguas"] = st.toggle("Techo a dos aguas", value=bool(state.get("dos_aguas", True)))


def ui_cableado(state: Dict[str, Any]) -> None:
    st.subheader("Cableado (referencial)")

    state["vac"] = st.selectbox("Voltaje AC (V)", [240.0, 208.0], index=0 if float(state.get("vac", 240.0)) == 240.0 else 1)
    state["dist_dc_m"] = st.number_input("Distancia DC panel→inversor (m)", value=float(state.get("dist_dc_m", 15.0)), min_value=1.0, step=1.0)
    state["dist_ac_m"] = st.number_input("Distancia AC inversor→tablero (m)", value=float(state.get("dist_ac_m", 25.0)), min_value=1.0, step=1.0)

    state["vdrop_obj_dc_pct"] = st.number_input("Caída objetivo DC (%)", value=float(state.get("vdrop_obj_dc_pct", 2.0)), min_value=0.5, step=0.5)
    state["vdrop_obj_ac_pct"] = st.number_input("Caída objetivo AC (%)", value=float(state.get("vdrop_obj_ac_pct", 2.0)), min_value=0.5, step=0.5)

    state["incluye_neutro_ac"] = st.toggle("Incluye neutro (AC)", value=bool(state.get("incluye_neutro_ac", False)))
    state["otros_ccc"] = st.number_input("Otros CCC en la misma tubería", value=int(state.get("otros_ccc", 0)), min_value=0, step=1)

    state["t_min_c"] = st.number_input("Temp mínima sitio (°C) para Voc frío", value=float(state.get("t_min_c", 10.0)), step=1.0)


def construir_parametros_cableado(state: Dict[str, Any]) -> ParametrosCableado:
    return ParametrosCableado(
        vac=float(state.get("vac", 240.0)),
        fases=1,
        fp=1.0,
        dist_dc_m=float(state.get("dist_dc_m", 15.0)),
        dist_ac_m=float(state.get("dist_ac_m", 25.0)),
        vdrop_obj_dc_pct=float(state.get("vdrop_obj_dc_pct", 2.0)),
        vdrop_obj_ac_pct=float(state.get("vdrop_obj_ac_pct", 2.0)),
        incluye_neutro_ac=bool(state.get("incluye_neutro_ac", False)),
        otros_ccc=int(state.get("otros_ccc", 0)),
        t_min_c=float(state.get("t_min_c", 10.0)),
    )
