# ui/ingenieria_electrica.py
from __future__ import annotations

from typing import List, Tuple, Dict, Any

import pandas as pd
import streamlit as st

from core.modelo import Datosproyecto
from core.orquestador import ejecutar_estudio
from ui.validaciones_ui import campos_faltantes_para_paso5
from ui.state_helpers import ensure_dict, merge_defaults, save_result_fingerprint


# ==========================================================
# Helpers UI
# ==========================================================

def _fmt(v, unit: str = "") -> str:
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        s = f"{v:.3f}".rstrip("0").rstrip(".")
        return f"{s} {unit}".rstrip() if unit else s
    return str(v)


def _asegurar_dict(ctx, nombre: str) -> dict:
    return ensure_dict(ctx, nombre, dict)

def _ui_inputs_electricos(e: dict):
    st.subheader("Parámetros eléctricos de instalación")

    # ==============================
    # Sistema eléctrico
    # ==============================
    c1, c2, c3 = st.columns(3)

    with c1:
        e["vac"] = st.number_input(
            "Voltaje AC (V)",
            min_value=100.0,
            max_value=600.0,
            value=float(e.get("vac", 240.0)),
            step=1.0,
        )

    with c2:
        opciones_fases = [1, 3]
        actual = int(e.get("fases", 1))
        idx = opciones_fases.index(actual) if actual in opciones_fases else 0
        e["fases"] = st.selectbox("Fases", opciones_fases, index=idx)

    with c3:
        e["fp"] = st.number_input(
            "Factor de potencia",
            min_value=0.80,
            max_value=1.00,
            value=float(e.get("fp", 1.0)),
            step=0.01,
        )

    # ==============================
    # Distancias y regulación
    # ==============================
    st.markdown("### Distancias y regulación")

    d1, d2 = st.columns(2)

    with d1:
        e["dist_dc_m"] = st.number_input(
            "Distancia DC (m)",
            min_value=1.0,
            max_value=2000.0,
            value=float(e.get("dist_dc_m", 15.0)),
            step=1.0,
        )

        e["vdrop_obj_dc_pct"] = st.number_input(
            "Regulación DC objetivo (%)",
            min_value=0.5,
            max_value=10.0,
            value=float(e.get("vdrop_obj_dc_pct", 2.0)),
            step=0.1,
        )

    with d2:
        e["dist_ac_m"] = st.number_input(
            "Distancia AC (m)",
            min_value=1.0,
            max_value=2000.0,
            value=float(e.get("dist_ac_m", 25.0)),
            step=1.0,
        )

        e["vdrop_obj_ac_pct"] = st.number_input(
            "Regulación AC objetivo (%)",
            min_value=0.5,
            max_value=10.0,
            value=float(e.get("vdrop_obj_ac_pct", 2.0)),
            step=0.1,
        )

    # ==============================
    # Condiciones NEC
    # ==============================
    st.markdown("### Condiciones de instalación")

    k1, k2, k3 = st.columns(3)

    with k1:
        e["t_min_c"] = st.number_input(
            "Temperatura mínima (°C)",
            min_value=-40.0,
            max_value=60.0,
            value=float(e.get("t_min_c", 10.0)),
            step=1.0,
        )

    with k2:
        e["incluye_neutro_ac"] = st.checkbox(
            "Incluye neutro en AC",
            value=bool(e.get("incluye_neutro_ac", False)),
        )

    with k3:
        e["otros_ccc"] = st.number_input(
            "Otros conductores activos en tubería",
            min_value=0,
            max_value=20,
            value=int(e.get("otros_ccc", 0)),
            step=1,
        )




# ==========================================================
# Defaults eléctricos
# ==========================================================

def _defaults_electrico(ctx) -> dict:
    e = _asegurar_dict(ctx, "electrico")
    merge_defaults(
        e,
        {
            "vac": 240.0,
            "fases": 1,
            "fp": 1.0,
            "dist_dc_m": 15.0,
            "dist_ac_m": 25.0,
            "vdrop_obj_dc_pct": 2.0,
            "vdrop_obj_ac_pct": 2.0,
            "t_min_c": 10.0,
        },
    )
    return e


# ==========================================================
# ctx → Datosproyecto
# ==========================================================

def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:
    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf = _asegurar_dict(ctx, "sistema_fv")

    consumo_12m = c.get("kwh_12m", [0.0] * 12)

    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),
        consumo_12m=[float(x) for x in consumo_12m],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 0)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 0)),
        prod_base_kwh_kwp_mes=float(sf.get("produccion_base_kwh_kwp_mes", 145)),
        factores_fv_12m=[float(x) for x in sf.get("factores_fv_12m", [1] * 12)],
        cobertura_objetivo=float(sf.get("cobertura_objetivo", 0.8)),
        costo_usd_kwp=float(sf.get("costo_usd_kwp", 1200)),
        tcambio=float(sf.get("tcambio", 27)),
        tasa_anual=float(sf.get("tasa_anual", 0.08)),
        plazo_anios=int(sf.get("plazo_anios", 10)),
        porcentaje_financiado=float(sf.get("porcentaje_financiado", 1)),
        om_anual_pct=float(sf.get("om_anual_pct", 0.01)),
    )

    setattr(p, "sistema_fv", dict(sf))
    setattr(p, "electrico", dict(_asegurar_dict(ctx, "electrico")))

    return p


# ==========================================================
# NEC Display (solo presentación)
# ==========================================================

def _mostrar_nec(pkg: dict):
    st.divider()
    st.subheader("Ingeniería NEC 2023")

    if not pkg:
        st.info("Sin resultados NEC.")
        return

    dc = pkg.get("dc") or {}
    ac = pkg.get("ac") or {}
    conductores = (pkg.get("conductores") or {}).get("circuitos") or []
    warnings = pkg.get("warnings") or []

    tabs = st.tabs(["⚡ DC", "🔌 AC", "🧵 Conductores", "⚠ Warnings"])

    with tabs[0]:
        st.metric("Vdc nominal", _fmt(dc.get("vdc_nom"), "V"))
        st.metric("Idc nominal", _fmt(dc.get("idc_nom"), "A"))
        st.metric("Potencia DC", _fmt(dc.get("potencia_dc_w"), "W"))

    with tabs[1]:
        st.metric("Potencia AC", _fmt(ac.get("potencia_ac_w"), "W"))
        st.metric("Voltaje", _fmt(ac.get("vac_ll") or ac.get("vac_ln"), "V"))
        st.metric("I nominal", _fmt(ac.get("iac_nom"), "A"))

    with tabs[2]:
        if not conductores:
            st.info("Sin datos de conductores.")
        else:
            rows = []
            for c in conductores:
                rows.append(
                    {
                        "Circuito": c.get("nombre"),
                        "Calibre": c.get("calibre"),
                        "I diseño (A)": c.get("i_diseno_a"),
                        "VD (%)": c.get("vd_pct"),
                        "Cumple": "✅" if c.get("cumple") else "❌",
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with tabs[3]:
        if not warnings:
            st.success("Sin advertencias.")
        else:
            for w in warnings:
                st.warning(w)


# ==========================================================
# RENDER
# ==========================================================

def render(ctx):

    e = _defaults_electrico(ctx)
    _ui_inputs_electricos(e)
    st.markdown("### Ingeniería eléctrica automática")

    faltantes = campos_faltantes_para_paso5(ctx)
    if faltantes:
        st.warning("Complete los datos requeridos antes de generar ingeniería.")

    if not st.button("Generar ingeniería", disabled=bool(faltantes)):
        return

    try:
        datos = _datosproyecto_desde_ctx(ctx)
        resultado = ejecutar_estudio(datos)

        save_result_fingerprint(ctx)

        st.success("Ingeniería generada correctamente.")

        # Mostrar sizing
        st.subheader("Sizing")
        st.json(resultado.get("sizing"))

        # Mostrar NEC
        wrapper = resultado.get("electrico_nec") or {}
        pkg = wrapper.get("paq") or {}
        _mostrar_nec(pkg)

        # Mostrar finanzas
        st.subheader("Finanzas")
        st.json(resultado.get("finanzas_lp"))

    except Exception as exc:
        st.error(f"No se pudo generar ingeniería: {exc}")


# ==========================================================
# VALIDAR PASO
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:
    errores = []

    if "resultado_proyecto" not in st.session_state:
        errores.append("Debe generar ingeniería.")

    return len(errores) == 0, errores
