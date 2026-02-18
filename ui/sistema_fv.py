# ui/sistema_fv.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import streamlit as st


# ==========================================================
# Defaults / Modelo UI
# ==========================================================

def _defaults_sistema_fv() -> Dict[str, Any]:
    return {
        # Radiación / recurso solar
        "hsp_kwh_m2_d": 5.2,          # horas sol pico (kWh/m²·día equivalente)
        "hsp_override": False,        # si el usuario forzó el valor

        # Geometría del arreglo
        "inclinacion_deg": 15,
        "azimut_deg": 180,            # 180 = Sur en convención 0=N, 90=E, 180=S, 270=O
        "orientacion_label": "Sur",

        # Condición de instalación
        "tipo_montaje": "Techo ventilado",   # afecta pérdidas térmicas en modelos avanzados
        "sombras_pct": 0.0,                  # pérdidas por sombras (0–20% típico)
        "perdidas_sistema_pct": 15.0,         # pérdidas globales (mismatch, suciedad, cableado, inversor, etc.)

        # Tu parámetro legado (si aún lo usas)
        "produccion_base_kwh_kwp_mes": 145.0, # puedes derivarlo luego desde HSP y pérdidas en core
    }


def _asegurar_dict(ctx, nombre: str) -> Dict[str, Any]:
    if not hasattr(ctx, nombre) or getattr(ctx, nombre) is None:
        setattr(ctx, nombre, {})
    d = getattr(ctx, nombre)
    if not isinstance(d, dict):
        setattr(ctx, nombre, {})
        d = getattr(ctx, nombre)
    return d


def _get_sf(ctx) -> Dict[str, Any]:
    sf = _asegurar_dict(ctx, "sistema_fv")
    for k, v in _defaults_sistema_fv().items():
        sf.setdefault(k, v)
    return sf


# ==========================================================
# Catálogos UI (valores + azimut)
# ==========================================================

def _opciones_orientacion() -> List[Dict[str, Any]]:
    # Convención: 0=N, 90=E, 180=S, 270=O
    return [
        {"label": "Sur (óptimo)", "azimut": 180},
        {"label": "Sureste", "azimut": 135},
        {"label": "Suroeste", "azimut": 225},
        {"label": "Este", "azimut": 90},
        {"label": "Oeste", "azimut": 270},
        {"label": "Norte (no recomendado)", "azimut": 0},
    ]


def _opciones_sombras() -> List[Dict[str, Any]]:
    return [
        {"label": "Sin sombras (0%)", "pct": 0.0},
        {"label": "Sombras ligeras (5%)", "pct": 5.0},
        {"label": "Sombras medias (10%)", "pct": 10.0},
        {"label": "Sombras severas (20%)", "pct": 20.0},
    ]


def _opciones_montaje() -> List[str]:
    return [
        "Techo ventilado",
        "Techo pegado (poca ventilación)",
        "Estructura elevada (suelo)",
    ]


# ==========================================================
# Render: secciones pequeñas
# ==========================================================

def _render_radiacion(sf: Dict[str, Any]) -> None:
    st.markdown("#### Recurso solar (HSP / Radiación)")

    c1, c2 = st.columns([1, 2])
    with c1:
        sf["hsp_override"] = st.checkbox(
            "Editar manualmente HSP",
            value=bool(sf["hsp_override"]),
            help="Si no, este valor debería venir de la ubicación (modelo futuro).",
        )

    with c2:
        st.caption("HSP típico en Honduras: 4.8–5.6 h/día (depende de zona, nubosidad y época).")

    disabled = not bool(sf["hsp_override"])
    sf["hsp_kwh_m2_d"] = st.number_input(
        "HSP (kWh/m²·día) / Horas sol pico",
        min_value=3.0,
        max_value=7.0,
        step=0.1,
        value=float(sf["hsp_kwh_m2_d"]),
        disabled=disabled,
    )




def _render_condiciones(sf: Dict[str, Any]) -> None:
    st.markdown("#### Condiciones de instalación")

    c1, c2, c3 = st.columns(3)

    with c1:
        sf["tipo_montaje"] = st.selectbox(
            "Tipo de montaje",
            options=_opciones_montaje(),
            index=_opciones_montaje().index(str(sf["tipo_montaje"])) if str(sf["tipo_montaje"]) in _opciones_montaje() else 0,
        )

    with c2:
        sombras = _opciones_sombras()
        sombras_labels = [x["label"] for x in sombras]

        # índice por pct guardado
        pct = float(sf.get("sombras_pct", 0.0))
        idx = 0
        for i, it in enumerate(sombras):
            if float(it["pct"]) == float(pct):
                idx = i
                break

        sel_label = st.selectbox("Sombras (pérdida)", options=sombras_labels, index=idx)
        sel = next(x for x in sombras if x["label"] == sel_label)
        sf["sombras_pct"] = float(sel["pct"])

    with c3:
        sf["perdidas_sistema_pct"] = st.number_input(
            "Pérdidas del sistema (%)",
            min_value=5.0,
            max_value=30.0,
            step=0.5,
            value=float(sf["perdidas_sistema_pct"]),
            help="Incluye mismatch, suciedad, cableado, inversor, etc. Típico 14–18%.",
        )


def _render_resumen(sf: Dict[str, Any]) -> None:
    st.divider()
    st.markdown("#### Resumen (entradas)")

    st.write(
        f"• HSP: **{sf['hsp_kwh_m2_d']:.1f}** h/día "
        f"{'(manual)' if sf['hsp_override'] else '(estimado)'}"
    )
    st.write(f"• Orientación: **{sf['orientacion_label']}** (azimut {int(sf['azimut_deg'])}°)")
    st.write(f"• Inclinación: **{int(sf['inclinacion_deg'])}°**")
    st.write(f"• Montaje: **{sf['tipo_montaje']}**")
    st.write(f"• Sombras: **{sf['sombras_pct']:.0f}%**")
    st.write(f"• Pérdidas del sistema: **{sf['perdidas_sistema_pct']:.1f}%**")


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


def _errores(sf: Dict[str, Any]) -> List[str]:
    errs: List[str] = []

    if float(sf.get("hsp_kwh_m2_d", 0.0)) <= 0:
        errs.append("HSP debe ser mayor que 0.")

    inc = int(sf.get("inclinacion_deg", 0))
    if inc < 0 or inc > 45:
        errs.append("Inclinación fuera de rango (0–45°).")

    az = int(sf.get("azimut_deg", -1))
    if az < 0 or az > 360:
        errs.append("Azimut fuera de rango (0–360°).")

    perd = float(sf.get("perdidas_sistema_pct", 0.0))
    if perd < 5.0 or perd > 30.0:
        errs.append("Pérdidas del sistema fuera de rango (5–30%).")

    sh = float(sf.get("sombras_pct", 0.0))
    if sh < 0.0 or sh > 30.0:
        errs.append("Sombras fuera de rango (0–30%).")

    return errs


def validar(ctx) -> Tuple[bool, List[str]]:
    sf = _get_sf(ctx)
    errs = _errores(sf)
    return (len(errs) == 0), errs
