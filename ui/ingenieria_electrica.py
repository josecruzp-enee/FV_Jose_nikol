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
        e["vac"] = st.number_input("Voltaje AC (V)", 100.0, 600.0, float(e.get("vac", 240.0)))

    with c2:
        e["fases"] = st.selectbox("Fases", [1, 3], index=0 if int(e.get("fases", 1)) == 1 else 1)

    with c3:
        e["fp"] = st.number_input("Factor de potencia", 0.80, 1.00, float(e.get("fp", 1.0)), step=0.01)

    st.markdown("### Distancias")

    d1, d2 = st.columns(2)

    with d1:
        e["dist_dc_m"] = st.number_input("Distancia DC (m)", 1.0, value=float(e.get("dist_dc_m", 15.0)))

    with d2:
        e["dist_ac_m"] = st.number_input("Distancia AC (m)", 1.0, value=float(e.get("dist_ac_m", 25.0)))


# ==========================================================
# ctx → DatosProyecto
# ==========================================================

def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:

    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf = _asegurar_dict(ctx, "sistema_fv")
    eq = _asegurar_dict(ctx, "equipos")

    consumo = c.get("kwh_12m", [0] * 12)

    # 🔴 FIX EQUIPOS (OBLIGATORIO PARA SIZING)
    if "panel_id" not in eq:
        eq["panel_id"] = "JA_550"  # ⚠️ usa un ID real de tu catálogo

    if "inversor_id" not in eq:
        eq["inversor_id"] = "HUAWEI_50K"  # ⚠️ usa uno real

    p = Datosproyecto(

        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),

        # 🔴 COORDENADAS
        lat=float(sf.get("latitud", 14.8)),
        lon=float(sf.get("longitud", -86.2)),

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

        instalacion_electrica=None
    )

    # 🔴 IMPORTANTE: pasar equipos al dominio
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

    st.json(nec)


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

        ctx.resultado_proyecto = resultado

        st.success("Ingeniería generada correctamente.")

        _mostrar_sizing(resultado.sizing)
        _mostrar_nec(resultado.nec)

    except Exception:

        import traceback

        st.error("Error en motor FV")
        st.code(traceback.format_exc())


# ==========================================================
# VALIDACIÓN
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    errores = []

    if not getattr(ctx, "resultado_proyecto", None):
        errores.append("Debe generar ingeniería.")

    return len(errores) == 0, errores
