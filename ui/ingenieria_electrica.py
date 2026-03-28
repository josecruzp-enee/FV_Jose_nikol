from __future__ import annotations

"""
PASO 5 — INGENIERÍA ELÉCTRICA
FV Engine (CORREGIDO MULTIZONA)
"""

from typing import List, Tuple
import streamlit as st

from core.dominio.modelo import Datosproyecto, InstalacionElectrica, Equipos
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
# ctx → DatosProyecto (🔥 CORREGIDO MULTIZONA)
# ==========================================================
def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:

    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf_raw = _asegurar_dict(ctx, "sistema_fv")
    eq = _asegurar_dict(ctx, "equipos")
    e = _asegurar_dict(ctx, "electrico")

    consumo = c.get("consumo_12m", [0] * 12)

    # ======================================================
    # BASE PROYECTO
    # ======================================================
    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),

        lat=float(sf_raw.get("latitud", 15.8250)),
        lon=float(sf_raw.get("longitud", -87.9500)),

        consumo_12m=[float(x) for x in consumo],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 5.50)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 400)),

        prod_base_kwh_kwp_mes=float(sf_raw.get("produccion_base_kwh_kwp_mes", 145)),
        factores_fv_12m=[float(x) for x in sf_raw.get("factores_fv_12m", [1] * 12)],
        cobertura_objetivo=float(sf_raw.get("cobertura_objetivo", 0.8)),

        costo_usd_kwp=float(sf_raw.get("costo_usd_kwp", 1200)),
        tcambio=float(sf_raw.get("tcambio", 27)),

        tasa_anual=float(sf_raw.get("tasa_anual", 0.08)),
        plazo_anios=int(sf_raw.get("plazo_anios", 10)),
        porcentaje_financiado=float(sf_raw.get("porcentaje_financiado", 1)),

        om_anual_pct=float(sf_raw.get("om_anual_pct", 0.01)),

        instalacion_electrica=InstalacionElectrica(
            vac=float(e.get("vac", 240.0)),
            fases=int(e.get("fases", 1)),
            fp=float(e.get("fp", 1.0)),
            dist_dc_m=float(e.get("dist_dc_m", 15.0)),
            dist_ac_m=float(e.get("dist_ac_m", 25.0)),
        )
    )

    # ======================================================
    # EQUIPOS
    # ======================================================
    p.equipos = Equipos(
        panel_id=eq.get("panel_id"),
        inversor_id=eq.get("inversor_id"),
    )

    # ======================================================
    # 🔥 NORMALIZACIÓN MULTIZONA (CLAVE)
    # ======================================================
    sf = {}

    if sf_raw.get("usar_zonas"):

        zonas_norm = []

        for z in sf_raw.get("zonas", []):

            if z.get("modo") == "Paneles":
                zonas_norm.append({
                    "n_paneles": int(z.get("n_paneles") or 0)
                })
            else:
                zonas_norm.append({
                    "area": float(z.get("area") or 0.0)
                })

        sf["modo"] = "multizona"
        sf["zonas"] = zonas_norm

    else:

        sizing = sf_raw.get("sizing_input", {})

        sf["modo"] = sizing.get("modo", "manual")
        sf["valor"] = sizing.get("valor", 0)

    p.sistema_fv = sf

    return p


# ==========================================================
# MOSTRAR SIZING
# ==========================================================
def _mostrar_sizing(sizing, sistema_fv):

    st.subheader("Sizing del sistema FV")

    modo = sistema_fv.get("modo", "manual")

    if modo == "multizona":
        st.info("Modo: Diseño por zonas")
    else:
        st.info("Modo: Diseño automático/manual")

    c1, c2, c3 = st.columns(3)

    c1.metric("Paneles", sizing.n_paneles)
    c2.metric("Potencia DC", f"{sizing.pdc_kw} kWp")
    c3.metric("Potencia AC", f"{sizing.kw_ac} kW")


# ==========================================================
# MOSTRAR ELECTRICAL
# ==========================================================
def _mostrar_electrical(electrical, paneles=None):

    st.subheader("Ingeniería eléctrica")

    if electrical is None:
        st.info("Sin resultados eléctricos.")
        return

    ok = getattr(electrical, "ok", False)

    st.success("Cálculo eléctrico correcto") if ok else st.error("Ingeniería eléctrica con errores")

    corrientes = getattr(electrical, "corrientes", None)
    conductores = getattr(electrical, "conductores", None)
    protecciones = getattr(electrical, "protecciones", None)

    if corrientes:
        st.markdown("### ⚡ Corrientes")
        c1, c2, c3 = st.columns(3)
        c1.metric("String", f"{getattr(corrientes.string, 'i_diseno_a', 0):.2f} A")
        c2.metric("MPPT", f"{getattr(corrientes.mppt, 'i_diseno_a', 0):.2f} A")
        c3.metric("AC", f"{getattr(corrientes.ac, 'i_diseno_a', 0):.2f} A")

    if conductores and hasattr(conductores, "tramos"):
        st.markdown("### 🧵 Conductores")
        dc = conductores.tramos.dc
        c1, c2, c3 = st.columns(3)
        c1.metric("Calibre", f"{dc.calibre} AWG")
        c2.metric("Ampacidad", f"{dc.ampacidad_ajustada_a} A")
        c3.metric("VD", f"{dc.vd_pct:.2f} %")

    if protecciones:
        st.markdown("### ⚠ Protecciones")
        c1, c2, c3 = st.columns(3)
        c1.metric("Breaker AC", f"{protecciones.ocpd_ac.tamano_a} A")
        c2.metric("Protección DC", f"{protecciones.ocpd_dc_array.tamano_a} A")
        c3.metric("Fusible", f"{protecciones.fusible_string.tamano_a} A")


# ==========================================================
# RENDER
# ==========================================================
def render(ctx):

    e = _asegurar_dict(ctx, "electrico")
    _ui_inputs_electricos(e)

    st.markdown("### Ingeniería eléctrica automática")

    if st.button("Generar ingeniería"):

        faltantes = campos_faltantes_para_paso5(ctx)

        if faltantes:
            st.error(f"Faltan datos obligatorios: {faltantes}")
            st.stop()

        try:
            datos = _datosproyecto_desde_ctx(ctx)

            deps = construir_dependencias()

            resultado = ejecutar_estudio(datos, deps)

            st.session_state["resultado_proyecto"] = resultado

            st.success("Ingeniería generada correctamente.")

        except Exception:
            import traceback
            st.error("Error en motor FV")
            st.code(traceback.format_exc())
            st.stop()

    resultado = st.session_state.get("resultado_proyecto")

    if resultado:
        _mostrar_sizing(resultado.sizing, resultado.sistema_fv)
        _mostrar_electrical(resultado.electrical, resultado.strings)


# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:

    errores = []

    if not st.session_state.get("resultado_proyecto"):
        errores.append("Debe generar ingeniería.")

    return len(errores) == 0, errores
