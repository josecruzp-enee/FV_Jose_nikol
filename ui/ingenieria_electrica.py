# ui/ingenieria_electrica.py
from __future__ import annotations

from typing import List, Tuple
import pandas as pd
import streamlit as st

from core.dominio.modelo import Datosproyecto
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.aplicacion.dependencias import construir_dependencias
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


# ==========================================================
# Inputs eléctricos
# ==========================================================

def _ui_inputs_electricos(e: dict):
    st.subheader("Parámetros eléctricos de instalación")

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
# ctx → Datosproyecto
# ==========================================================

def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:
    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf = _asegurar_dict(ctx, "sistema_fv")
    eq = _asegurar_dict(ctx, "equipos")

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

    p.sistema_fv = dict(sf)
    p.electrico = dict(_asegurar_dict(ctx, "electrico"))
    p.equipos = dict(eq)

    return p


# ==========================================================
# Mostrar sizing claro
# ==========================================================

def _mostrar_sizing(sizing):

    st.subheader("Sizing del sistema FV")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Paneles", sizing.get("n_paneles"))

    with c2:
        st.metric("Potencia DC", f"{sizing.get('kwp_dc')} kWp")

    with c3:
        st.metric("Potencia AC", f"{sizing.get('pac_kw')} kW")

    paneles = sizing.get("n_paneles")
    paneles_por_string = sizing.get("paneles_por_string")

    if paneles and paneles_por_string:

        n_strings = paneles // paneles_por_string

        st.markdown("### Configuración de strings")

        s1, s2 = st.columns(2)

        with s1:
            st.metric("Paneles por string", paneles_por_string)

        with s2:
            st.metric("Número de strings", n_strings)

def _mostrar_nec(nec):

    st.subheader("Ingeniería NEC 2023")

    if not nec:
        st.info("Sin resultados NEC.")
        return

    paq = nec.get("paq", {})
    dc = paq.get("dc", {})
    ac = paq.get("ac", {})
    ocpd = paq.get("ocpd", {})
    conductores = paq.get("conductores", {}).get("circuitos", [])
    warnings = paq.get("warnings", [])

    tabs = st.tabs(["⚡ DC", "🔌 AC", "🧵 Conductores", "⚠ Warnings"])

    # =========================
    # DC
    # =========================
    with tabs[0]:

        c1, c2 = st.columns(2)

        with c1:
            st.metric("Voltaje DC", _fmt(dc.get("vdc_nom"), "V"))

        with c2:
            st.metric("Corriente DC", _fmt(dc.get("idc_nom"), "A"))

        st.metric("Potencia DC", _fmt(dc.get("potencia_dc_w"), "W"))

    # =========================
    # AC
    # =========================
    with tabs[1]:

        c1, c2 = st.columns(2)

        with c1:
            st.metric("Voltaje AC", _fmt(ac.get("vac_ll"), "V"))

        with c2:
            st.metric("Corriente AC", _fmt(ac.get("iac_nom"), "A"))

        st.metric("Potencia AC", _fmt(ac.get("potencia_ac_w"), "W"))

        breaker = ocpd.get("breaker_ac", {})

        if breaker:

            st.markdown("### Protección AC")

            st.metric(
                "Breaker requerido",
                _fmt(breaker.get("tamano_a"), "A"),
            )

    # =========================
    # Conductores
    # =========================
    with tabs[2]:

        if not conductores:
            st.info("Sin datos de conductores")

        else:

            filas = []

            for c in conductores:

                filas.append(
                    {
                        "Circuito": c.get("nombre"),
                        "Calibre": c.get("calibre"),
                        "I diseño (A)": _fmt(c.get("i_diseno_a"), "A"),
                        "VD (%)": _fmt(c.get("vd_pct"), "%"),
                        "Cumple": "✅" if c.get("cumple") else "❌",
                    }
                )

            df = pd.DataFrame(filas)

            st.dataframe(df, use_container_width=True)

    # =========================
    # Warnings
    # =========================
    with tabs[3]:

        if not warnings:
            st.success("Sin advertencias")
        else:
            for w in warnings:
                st.warning(w)

# ==========================================================
# RENDER
# ==========================================================

def render(ctx):

    e = _asegurar_dict(ctx, "electrico")
    _ui_inputs_electricos(e)

    st.markdown("### Ingeniería eléctrica automática")

    faltantes = campos_faltantes_para_paso5(ctx)
    if faltantes:
        st.warning("Complete los datos requeridos antes de generar ingeniería.")

    if not st.button("Generar ingeniería", disabled=bool(faltantes)):
        return

    try:

        datos = _datosproyecto_desde_ctx(ctx)
        deps = construir_dependencias()

        resultado = ejecutar_estudio(datos, deps)

        if hasattr(resultado, "__dict__"):
            resultado = resultado.__dict__

        ctx.resultado_proyecto = resultado

        st.success("Ingeniería generada correctamente.")

        sizing = resultado.get("sizing", {})
        nec = resultado.get("nec", {})
        financiero = resultado.get("financiero", {})

        _mostrar_sizing(sizing)

        _mostrar_nec(nec)

        st.subheader("Finanzas")
        st.json(financiero)

    except Exception as exc:
        st.error(f"No se pudo generar ingeniería: {exc}")


# ==========================================================
# VALIDAR PASO
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    errores = []

    if not getattr(ctx, "resultado_proyecto", None):
        errores.append("Debe generar ingeniería.")

    return len(errores) == 0, errores
