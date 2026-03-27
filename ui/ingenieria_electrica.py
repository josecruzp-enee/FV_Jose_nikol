from __future__ import annotations

"""
PASO 5 — INGENIERÍA ELÉCTRICA
FV Engine
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
# ctx → DatosProyecto
# ==========================================================

def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:

    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf = _asegurar_dict(ctx, "sistema_fv")
    eq = _asegurar_dict(ctx, "equipos")
    e = _asegurar_dict(ctx, "electrico")

    consumo = c.get("kwh_12m", [0] * 12)

    if "panel_id" not in eq:
        eq["panel_id"] = "JA_550"

    if "inversor_id" not in eq:
        eq["inversor_id"] = "HUAWEI_50K"

    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),

        lat=float(sf.get("latitud", 15.8250)),
        lon=float(sf.get("longitud", -87.9500)),

        consumo_12m=[float(x) for x in consumo],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 5.50)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 400)),

        prod_base_kwh_kwp_mes=float(sf.get("produccion_base_kwh_kwp_mes", 145)),
        factores_fv_12m=[float(x) for x in sf.get("factores_fv_12m", [1] * 12)],
        cobertura_objetivo=float(sf.get("cobertura_objetivo", 0.8)),

        costo_usd_kwp=float(sf.get("costo_usd_kwp", 1200)),
        tcambio=float(sf.get("tcambio", 27)),

        tasa_anual=float(sf.get("tasa_anual", 0.08)),
        plazo_anios=int(sf.get("plazo_anios", 10)),
        porcentaje_financiado=float(sf.get("porcentaje_financiado", 1)),

        om_anual_pct=float(sf.get("om_anual_pct", 0.01)),

        instalacion_electrica=InstalacionElectrica(
            vac=float(e.get("vac", 240.0)),
            fases=int(e.get("fases", 1)),
            fp=float(e.get("fp", 1.0)),
            dist_dc_m=float(e.get("dist_dc_m", 15.0)),
            dist_ac_m=float(e.get("dist_ac_m", 25.0)),
        )
    )

    p.equipos = Equipos(
        panel_id=eq.get("panel_id"),
        inversor_id=eq.get("inversor_id"),
    )

    p.sistema_fv = dict(sf)

    return p


# ==========================================================
# MOSTRAR SIZING
# ==========================================================

def _mostrar_sizing(sizing, sistema_fv):

    st.subheader("Sizing del sistema FV")

    modo = sistema_fv.get("modo_diseno", "manual")

    st.info("Modo: Diseño por zonas" if modo == "zonas" else "Modo: Diseño automático/manual")

    c1, c2, c3 = st.columns(3)

    c1.metric("Paneles", sizing.n_paneles)
    c2.metric("Potencia DC", f"{sizing.pdc_kw} kWp")
    c3.metric("Potencia AC", f"{sizing.kw_ac} kW")


# ==========================================================
# MOSTRAR ELECTRICAL + MULTIZONA
# ==========================================================

def _mostrar_electrical(electrical, paneles=None):

    st.subheader("Ingeniería eléctrica")

    if electrical is None:
        st.info("Sin resultados eléctricos.")
        return

    def _get(obj, key, default=None):
        return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

    ok = _get(electrical, "ok", False)

    st.success("Cálculo eléctrico correcto") if ok else st.error("Ingeniería eléctrica con errores")

    warnings = _get(electrical, "warnings", [])
    if warnings:
        st.warning("\n".join(warnings))

    corrientes = _get(electrical, "corrientes")
    conductores = _get(electrical, "conductores")
    protecciones = _get(electrical, "protecciones")

    # ⚡ CORRIENTES
    if corrientes:
        st.markdown("### ⚡ Corrientes")
        c1, c2, c3 = st.columns(3)
        c1.metric("String", f"{_get(corrientes.string, 'i_diseno_a', 0):.2f} A")
        c2.metric("MPPT", f"{_get(corrientes.mppt, 'i_diseno_a', 0):.2f} A")
        c3.metric("AC", f"{_get(corrientes.ac, 'i_diseno_a', 0):.2f} A")

    # 🧵 CONDUCTORES
    if conductores and hasattr(conductores, "tramos"):
        st.markdown("### 🧵 Conductores")
        dc = conductores.tramos.dc
        c1, c2, c3 = st.columns(3)
        c1.metric("Calibre", f"{dc.calibre} AWG")
        c2.metric("Ampacidad", f"{dc.ampacidad_ajustada_a} A")
        c3.metric("VD", f"{dc.vd_pct:.2f} %")

    # ⚠ PROTECCIONES
    if protecciones:
        st.markdown("### ⚠ Protecciones")
        c1, c2, c3 = st.columns(3)
        c1.metric("Breaker AC", f"{protecciones.ocpd_ac.tamano_a} A")
        c2.metric("Protección DC", f"{protecciones.ocpd_dc_array.tamano_a} A")
        c3.metric("Fusible", f"{protecciones.fusible_string.tamano_a} A")

    # 🧭 MULTIZONA
    try:
        zonas = getattr(paneles, "meta", {}).get("zonas", [])
    except:
        zonas = []

    if zonas:
        st.markdown("---")
        st.markdown("## 🧭 Detalle por zonas")

        for z in zonas:
            with st.expander(f"Zona {z.get('zona')}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Paneles", z.get("paneles"))
                c2.metric("Potencia", f"{z.get('pdc_kw', 0):.2f} kW")
                c3.metric("Strings", z.get("strings"))

                c4, c5 = st.columns(2)
                if z.get("vdc"):
                    c4.metric("Voltaje", f"{z['vdc']:.1f} V")
                if z.get("idc"):
                    c5.metric("Corriente", f"{z['idc']:.2f} A")


# ==========================================================
# RENDER
# ==========================================================
def render(ctx):

    # ==========================================================
    # INPUTS
    # ==========================================================
    e = _asegurar_dict(ctx, "electrico")
    _ui_inputs_electricos(e)

    st.markdown("### Ingeniería eléctrica automática")

    # ==========================================================
    # BOTÓN (SIN BLOQUEO)
    # ==========================================================
    if st.button("Generar ingeniería"):

        faltantes = campos_faltantes_para_paso5(ctx)

        # 🔴 VALIDACIÓN EN EJECUCIÓN (NO BLOQUEA BOTÓN)
        if faltantes:
            st.error(f"Faltan datos obligatorios: {faltantes}")
            st.stop()

        try:
            datos = _datosproyecto_desde_ctx(ctx)
            deps = construir_dependencias()

            resultado = ejecutar_estudio(datos, deps)

            if resultado is None:
                st.error("El motor devolvió None")
                st.stop()

            # ✅ GUARDAR RESULTADO
            st.session_state["resultado_proyecto"] = resultado

            st.success("Ingeniería generada correctamente.")

        except Exception:
            import traceback
            st.error("Error en motor FV")
            st.code(traceback.format_exc())
            st.stop()

    # ==========================================================
    # MOSTRAR RESULTADOS
    # ==========================================================
    resultado = st.session_state.get("resultado_proyecto")

    if resultado:

        _mostrar_sizing(resultado.sizing, ctx.sistema_fv)

        # 🔥 DEBUG OPCIONAL (puedes quitar luego)
        # st.write("DEBUG ELECTRICAL:", resultado.electrical)

        _mostrar_electrical(resultado.electrical, resultado.strings)
# ==========================================================
# VALIDACIÓN
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:
    errores = []
    if not st.session_state.get("resultado_proyecto"):
        errores.append("Debe generar ingeniería.")
    return len(errores) == 0, errores
