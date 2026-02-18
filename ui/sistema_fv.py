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
        "hsp_kwh_m2_d": 5.2,
        "hsp_override": False,

        # Geometría (compat)
        "inclinacion_deg": 15,
        "azimut_deg": 180,                 # 0=N, 90=E, 180=S, 270=O
        "orientacion_label": "Sur (óptimo)",

        # Condición de instalación
        "tipo_montaje": "Techo ventilado",
        "sombras_pct": 0.0,
        "perdidas_sistema_pct": 15.0,

        # Legado
        "produccion_base_kwh_kwp_mes": 145.0,
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
    _sf_defaults_geometria(sf)
    return sf


# ==========================================================
# Catálogos UI
# ==========================================================

def _opciones_orientacion() -> List[Dict[str, Any]]:
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
# Geometría — defaults + helpers cortos
# ==========================================================

def _sf_defaults_geometria(sf: Dict[str, Any]) -> None:
    sf.setdefault("tipo_superficie", "Un plano (suelo/losa/estructura)")

    # plano único
    sf.setdefault("azimut_deg", 180)

    # dos aguas
    sf.setdefault("azimut_a_deg", 90)
    sf.setdefault("azimut_b_deg", 270)
    sf.setdefault("reparto_pct_a", 50.0)

    # inclinación
    sf.setdefault("tilt_modo", "auto")  # auto | manual
    sf.setdefault("tilt_techo", "Techo residencial")
    sf.setdefault("inclinacion_deg", 15)


def _ui_select_orientacion(label_widget: str, az_actual: int, *, key: str) -> Tuple[str, int]:
    opciones = _opciones_orientacion()
    labels = [o["label"] for o in opciones]

    idx = 0
    for i, o in enumerate(opciones):
        if int(o["azimut"]) == int(az_actual):
            idx = i
            break

    sel_label = st.selectbox(label_widget, options=labels, index=idx, key=key)
    sel = next(o for o in opciones if o["label"] == sel_label)
    return str(sel_label), int(sel["azimut"])


def _ui_tipo_superficie(sf: Dict[str, Any]) -> None:
    sf["tipo_superficie"] = st.selectbox(
        "Tipo de superficie",
        options=["Un plano (suelo/losa/estructura)", "Techo dos aguas"],
        index=0 if sf.get("tipo_superficie") != "Techo dos aguas" else 1,
        key="sf_tipo_superficie",
        help="Dos aguas: dos orientaciones + reparto de paneles por cada agua.",
    )


def _ui_orientacion_plano(sf: Dict[str, Any]) -> None:
    label, az = _ui_select_orientacion("Orientación", int(sf.get("azimut_deg", 180)), key="sf_orientacion")
    sf["orientacion_label"] = label
    sf["azimut_deg"] = az


def _ui_orientacion_dos_aguas(sf: Dict[str, Any]) -> None:
    st.caption("Agua A")
    label_a, az_a = _ui_select_orientacion("Orientación agua A", int(sf.get("azimut_a_deg", 90)), key="sf_orient_a")
    sf["azimut_a_deg"] = az_a

    st.caption("Agua B")
    label_b, az_b = _ui_select_orientacion("Orientación agua B", int(sf.get("azimut_b_deg", 270)), key="sf_orient_b")
    sf["azimut_b_deg"] = az_b

    sf["reparto_pct_a"] = float(
        st.number_input(
            "Reparto paneles en agua A (%)",
            min_value=0.0,
            max_value=100.0,
            step=5.0,
            value=float(sf.get("reparto_pct_a", 50.0)),
            key="sf_reparto_a",
        )
    )
    st.write(f"Reparto agua B: **{100.0 - sf['reparto_pct_a']:.0f}%**")

    sf["orientacion_label"] = f"Dos aguas: {label_a} / {label_b}"

    # compat: resto del sistema hoy espera un azimut único
    sf["azimut_deg"] = int(sf["azimut_a_deg"])


def _ui_inclinacion(sf: Dict[str, Any]) -> None:
    modo = st.radio(
        "Definir inclinación",
        options=["Automática (por tipo de techo)", "Manual (°)"],
        index=0 if sf.get("tilt_modo") == "auto" else 1,
        horizontal=True,
        key="sf_tilt_modo",
    )
    sf["tilt_modo"] = "auto" if "Automática" in modo else "manual"

    if sf["tilt_modo"] == "auto":
        tipos = ["Techo plano", "Techo residencial", "Techo pronunciado"]
        actual = str(sf.get("tilt_techo", "Techo residencial"))
        if actual not in tipos:
            actual = "Techo residencial"
        tipo_techo = st.selectbox("Tipo de techo", options=tipos, index=tipos.index(actual), key="sf_tilt_techo")
        sf["tilt_techo"] = tipo_techo

        defaults = {"Techo plano": 12, "Techo residencial": 20, "Techo pronunciado": 30}
        sf["inclinacion_deg"] = int(defaults[tipo_techo])
        st.caption(f"Inclinación sugerida: {sf['inclinacion_deg']}° (modo manual si la quieres exacta).")
    else:
        sf["inclinacion_deg"] = int(
            st.number_input(
                "Inclinación (°)",
                min_value=0,
                max_value=45,
                step=1,
                value=int(sf.get("inclinacion_deg", 15)),
                key="sf_inclinacion_manual",
            )
        )


def _render_geometria(sf: Dict[str, Any]) -> None:
    st.markdown("#### Geometría del arreglo")

    _ui_tipo_superficie(sf)

    c1, c2 = st.columns(2)
    with c1:
        if sf["tipo_superficie"] == "Techo dos aguas":
            _ui_orientacion_dos_aguas(sf)
        else:
            _ui_orientacion_plano(sf)

    with c2:
        _ui_inclinacion(sf)


# ==========================================================
# Render: otras secciones
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

    sf["hsp_kwh_m2_d"] = st.number_input(
        "HSP (kWh/m²·día) / Horas sol pico",
        min_value=3.0,
        max_value=7.0,
        step=0.1,
        value=float(sf["hsp_kwh_m2_d"]),
        disabled=not bool(sf["hsp_override"]),
    )


def _render_condiciones(sf: Dict[str, Any]) -> None:
    st.markdown("#### Condiciones de instalación")

    c1, c2, c3 = st.columns(3)
    with c1:
        opciones = _opciones_montaje()
        actual = str(sf.get("tipo_montaje", opciones[0]))
        idx = opciones.index(actual) if actual in opciones else 0
        sf["tipo_montaje"] = st.selectbox("Tipo de montaje", options=opciones, index=idx)

    with c2:
        sombras = _opciones_sombras()
        labels = [x["label"] for x in sombras]
        pct = float(sf.get("sombras_pct", 0.0))
        idx = next((i for i, it in enumerate(sombras) if float(it["pct"]) == pct), 0)
        sel_label = st.selectbox("Sombras (pérdida)", options=labels, index=idx)
        sel = next(x for x in sombras if x["label"] == sel_label)
        sf["sombras_pct"] = float(sel["pct"])

    with c3:
        sf["perdidas_sistema_pct"] = st.number_input(
            "Pérdidas del sistema (%)",
            min_value=5.0,
            max_value=30.0,
            step=0.5,
            value=float(sf["perdidas_sistema_pct"]),
        )


def _render_resumen(sf: Dict[str, Any]) -> None:
    st.divider()
    st.markdown("#### Resumen (entradas)")

    st.write(
        f"• HSP: **{sf['hsp_kwh_m2_d']:.1f}** h/día "
        f"{'(manual)' if sf['hsp_override'] else '(estimado)'}"
    )
    st.write(f"• Superficie: **{sf['tipo_superficie']}**")
    st.write(f"• Orientación: **{sf['orientacion_label']}** (azimut compat {int(sf['azimut_deg'])}°)")
    if sf["tipo_superficie"] == "Techo dos aguas":
        st.write(f"  - Agua A: {int(sf['azimut_a_deg'])}° | reparto {sf['reparto_pct_a']:.0f}%")
        st.write(f"  - Agua B: {int(sf['azimut_b_deg'])}° | reparto {100.0 - sf['reparto_pct_a']:.0f}%")
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
