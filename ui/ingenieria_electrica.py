from __future__ import annotations

"""
PASO 5 — INGENIERÍA ELÉCTRICA
FV Engine
"""

from typing import List, Tuple
import pandas as pd
import streamlit as st

from core.dominio.modelo import Datosproyecto
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.aplicacion.dependencias import construir_dependencias

from ui.validaciones_ui import campos_faltantes_para_paso5
from ui.state_helpers import ensure_dict


# ==========================================================
# UTILIDADES
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
# INPUTS ELÉCTRICOS
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
        )

    with c2:
        e["fases"] = st.selectbox(
            "Fases",
            [1, 3],
            index=0 if int(e.get("fases", 1)) == 1 else 1,
        )

    with c3:
        e["fp"] = st.number_input(
            "Factor de potencia",
            min_value=0.80,
            max_value=1.00,
            value=float(e.get("fp", 1.0)),
            step=0.01,
        )

    st.markdown("### Distancias")

    d1, d2 = st.columns(2)

    with d1:
        e["dist_dc_m"] = st.number_input(
            "Distancia DC (m)",
            min_value=1.0,
            value=float(e.get("dist_dc_m", 15.0)),
        )

    with d2:
        e["dist_ac_m"] = st.number_input(
            "Distancia AC (m)",
            min_value=1.0,
            value=float(e.get("dist_ac_m", 25.0)),
        )


# ==========================================================
# ctx → DatosProyecto
# ==========================================================

def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:

    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf = _asegurar_dict(ctx, "sistema_fv")
    eq = _asegurar_dict(ctx, "equipos")

    consumo = c.get("kwh_12m", [0] * 12)

    p = Datosproyecto(

        cliente=str(dc.get("cliente", "")),

        ubicacion=str(dc.get("ubicacion", "")),

        consumo_12m=[float(x) for x in consumo],

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
# MOSTRAR SIZING
# ==========================================================

def _mostrar_sizing(sizing):

    st.subheader("Sizing del sistema FV")

    c1, c2, c3 = st.columns(3)

    c1.metric("Paneles", sizing.n_paneles)

    c2.metric("Potencia DC", f"{sizing.pdc_kw} kWp")

    c3.metric("Potencia AC", f"{sizing.kw_ac} kW")


# ==========================================================
# MOSTRAR NEC
# ==========================================================

def _mostrar_nec(nec):

    st.subheader("Ingeniería eléctrica (NEC)")

    if not nec:
        st.info("Sin resultados NEC.")
        return

    st.subheader("DEBUG NEC")
    st.json(nec)

    paquete = nec.get("paquete_nec", {})

    corrientes = paquete.get("corrientes", {})
    protecciones = paquete.get("protecciones", {})
    conductores = paquete.get("conductores", {}).get("circuitos", [])

    dc = corrientes.get("dc_total", {})
    ac = corrientes.get("ac", {})

    tabs = st.tabs(["DC", "AC", "Conductores"])

    with tabs[0]:

        st.metric(
            "Corriente DC operación",
            _fmt(dc.get("i_operacion_a"), "A")
        )

        st.metric(
            "Corriente DC diseño NEC",
            _fmt(dc.get("i_diseno_a"), "A")
        )

    with tabs[1]:

        st.metric(
            "Corriente AC operación",
            _fmt(ac.get("i_operacion_a"), "A")
        )

        st.metric(
            "Corriente AC diseño",
            _fmt(ac.get("i_diseno_a"), "A")
        )

        breaker = protecciones.get("breaker_ac", {})

        if breaker:

            st.metric(
                "Breaker AC",
                _fmt(breaker.get("tamano_a"), "A")
            )

    with tabs[2]:

        if not conductores:
            st.info("Sin datos de conductores")
            return

        filas = []

        for c in conductores:

            filas.append({

                "Circuito": c.get("nombre"),
                "Calibre": c.get("calibre"),
                "I diseño": _fmt(c.get("i_diseno_a"), "A"),
                "Ampacidad": _fmt(c.get("ampacidad_ajustada_a"), "A"),
                "VD": _fmt(c.get("vd_pct"), "%"),

            })

        df = pd.DataFrame(filas)

        st.dataframe(df, use_container_width=True)


# ==========================================================
# RENDER PRINCIPAL
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

        ctx.datos_proyecto = datos

        deps = construir_dependencias()

        resultado = ejecutar_estudio(datos, deps)
        import streamlit as st
        st.write("DEBUG TIPO RESULTADO:")
        st.write(type(resultado))

        if isinstance(resultado, dict):
            st.error("⚠️ ERROR: resultado es dict")
        else:
            st.success("resultado es objeto correcto")

        st.write(resultado)


        
        ctx.resultado_proyecto = resultado

        st.success("Ingeniería generada correctamente.")

        _mostrar_sizing(resultado.sizing)

        _mostrar_nec(resultado.nec)

    except Exception as exc:

        st.error(f"No se pudo generar ingeniería: {exc}")


# ==========================================================
# VALIDACIÓN DEL PASO
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    errores = []

    if not getattr(ctx, "resultado_proyecto", None):

        errores.append("Debe generar ingeniería.")

    return len(errores) == 0, errores
