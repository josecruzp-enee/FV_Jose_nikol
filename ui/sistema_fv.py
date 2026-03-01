# ui/sistema_fv.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import streamlit as st
from ui.state_helpers import ensure_dict, merge_defaults

from electrical.energia.energia_fv import (
    normalizar_sistema_fv,
    preview_generacion_anual,
)

# ==========================================================
# Defaults
# ==========================================================

def _defaults_sistema_fv() -> Dict[str, Any]:
    return {
        "hsp_kwh_m2_d": 5.2,
        "hsp_override": False,
        "inclinacion_deg": 15,
        "azimut_deg": 180,
        "orientacion_label": "Sur (óptimo)",
        "tipo_superficie": "Un plano (suelo/losa/estructura)",
        "azimut_a_deg": 90,
        "azimut_b_deg": 270,
        "reparto_pct_a": 50.0,
        "tilt_modo": "auto",
        "tilt_techo": "Techo residencial",
        "tipo_montaje": "Techo ventilado",
        "sombras_pct": 0.0,
        "perdidas_sistema_pct": 15.0,
        "kwp_preview": 5.0,
    }


def _asegurar_dict(ctx, nombre: str) -> Dict[str, Any]:
    return ensure_dict(ctx, nombre, dict)


def _get_sf(ctx) -> Dict[str, Any]:
    sf = _asegurar_dict(ctx, "sistema_fv")
    merge_defaults(sf, _defaults_sistema_fv())
    return sf


# ==========================================================
# Render secciones
# ==========================================================

def _render_radiacion(sf: Dict[str, Any]) -> None:
    st.markdown("#### Recurso solar (HSP)")

    sf["hsp_override"] = st.checkbox(
        "Editar manualmente HSP",
        value=bool(sf.get("hsp_override", False)),
        key="sf_hsp_override",
    )

    sf["hsp_kwh_m2_d"] = st.number_input(
        "HSP (kWh/m²·día)",
        min_value=3.0,
        max_value=7.0,
        step=0.1,
        value=float(sf.get("hsp_kwh_m2_d", 5.2)),
        disabled=not bool(sf.get("hsp_override", False)),
        key="sf_hsp",
    )


def _render_geometria(sf: Dict[str, Any]) -> None:
    st.markdown("#### Geometría del arreglo")

    sf["tipo_superficie"] = st.selectbox(
        "Tipo de superficie",
        options=["Un plano (suelo/losa/estructura)", "Techo dos aguas"],
        index=0 if sf.get("tipo_superficie") != "Techo dos aguas" else 1,
    )

    sf["azimut_deg"] = st.number_input(
        "Azimut (°)",
        min_value=0,
        max_value=360,
        value=int(sf.get("azimut_deg", 180)),
    )

    sf["inclinacion_deg"] = st.number_input(
        "Inclinación (°)",
        min_value=0,
        max_value=45,
        value=int(sf.get("inclinacion_deg", 15)),
    )


def _render_condiciones(sf: Dict[str, Any]) -> None:
    st.markdown("#### Condiciones de instalación")

    sf["sombras_pct"] = st.number_input(
        "Sombras (%)",
        min_value=0.0,
        max_value=30.0,
        step=1.0,
        value=float(sf.get("sombras_pct", 0.0)),
    )

    sf["perdidas_sistema_pct"] = st.number_input(
        "Pérdidas del sistema (%)",
        min_value=5.0,
        max_value=30.0,
        step=0.5,
        value=float(sf.get("perdidas_sistema_pct", 15.0)),
    )


def _render_resumen(sf: Dict[str, Any]) -> None:
    st.divider()
    st.markdown("#### Resumen (entradas)")

    st.write(f"HSP: {sf['hsp_kwh_m2_d']:.1f} h/día")
    st.write(f"Azimut: {sf['azimut_deg']}°")
    st.write(f"Inclinación: {sf['inclinacion_deg']}°")
    st.write(f"Sombras: {sf['sombras_pct']}%")
    st.write(f"Pérdidas: {sf['perdidas_sistema_pct']}%")


# ==========================================================
# Preview energético (usa dominio energía)
# ==========================================================

def _render_grafica_teorica(sf: Dict[str, Any]) -> None:
    st.divider()
    st.markdown("#### Gráfica teórica de generación FV (preview)")

    import matplotlib.pyplot as plt

    sf = normalizar_sistema_fv(sf)
    preview = preview_generacion_anual(sf)

    gen = preview["gen_mes"]
    total = preview["total_kwh_anual"]
    pr = preview["pr"]

    meses = list(range(1, 13))

    fig, ax = plt.subplots()
    ax.bar(meses, gen)
    ax.set_xticks(meses)
    ax.set_xlabel("Mes")
    ax.set_ylabel("Generación estimada (kWh/mes)")
    ax.set_title(f"Estimación anual: {total:,.0f} kWh/año")

    st.pyplot(fig, clear_figure=True)

    st.caption(f"Modelo simplificado preview. PR={pr:.3f}")


# ==========================================================
# API del paso
# ==========================================================

def render(ctx) -> None:
    st.markdown("### Sistema Fotovoltaico")

    sf = _get_sf(ctx)

    _render_radiacion(sf)
    _render_geometria(sf)
    _render_condiciones(sf)
    _render_resumen(sf)
    _render_grafica_teorica(sf)


def validar(ctx) -> Tuple[bool, List[str]]:
    sf = _get_sf(ctx)
    errs: List[str] = []

    if float(sf.get("hsp_kwh_m2_d", 0)) <= 0:
        errs.append("HSP debe ser mayor que 0.")

    if int(sf.get("inclinacion_deg", 0)) < 0:
        errs.append("Inclinación inválida.")

    return (len(errs) == 0), errs
