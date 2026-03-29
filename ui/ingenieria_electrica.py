from __future__ import annotations

from typing import List, Tuple
import streamlit as st

from core.dominio.modelo import Datosproyecto, InstalacionElectrica, Equipos
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.aplicacion.dependencias import construir_dependencias

from ui.state_helpers import ensure_dict


# ==========================================================
# UTIL
# ==========================================================
def _asegurar_dict(ctx, nombre: str) -> dict:
    return ensure_dict(ctx, nombre, dict)


# ==========================================================
# INPUTS
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
# DATOS PROYECTO
# ==========================================================
def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:

    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf_raw = _asegurar_dict(ctx, "sistema_fv")
    eq = _asegurar_dict(ctx, "equipos")
    e = _asegurar_dict(ctx, "electrico")

    consumo = c.get("consumo_12m", [0]*12)

    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),

        lat=float(sf_raw.get("latitud", 15.8250)),
        lon=float(sf_raw.get("longitud", -87.9500)),

        consumo_12m=[float(x) for x in consumo],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 5.50)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 400)),

        prod_base_kwh_kwp_mes=float(sf_raw.get("produccion_base_kwh_kwp_mes", 145)),
        factores_fv_12m=[float(x) for x in sf_raw.get("factores_fv_12m", [1]*12)],
        cobertura_objetivo=float(sf_raw.get("cobertura_objetivo", 0.8)),

        costo_usd_kwp=float(sf_raw.get("costo_usd_kwp", 1200)),
        tcambio=float(sf_raw.get("tcambio", 27)),

        tasa_anual=float(sf_raw.get("tasa_anual", 0.08)),
        plazo_anios=int(sf_raw.get("plazo_anios", 10)),
        porcentaje_financiado=float(sf_raw.get("porcentaje_financiado", 1)),

        instalacion_electrica=InstalacionElectrica(
            vac=float(e.get("vac", 240)),
            fases=int(e.get("fases", 1)),
            fp=float(e.get("fp", 1.0)),
            dist_dc_m=float(e.get("dist_dc_m", 15)),
            dist_ac_m=float(e.get("dist_ac_m", 25)),
        )
    )

    # EQUIPOS
    p.equipos = Equipos(
        panel_id=eq.get("panel_id"),
        inversor_id=eq.get("inversor_id"),
    )

    # MULTIZONA
    if sf_raw.get("usar_zonas"):

        zonas = []
        for z in sf_raw.get("zonas", []):
            zonas.append({"n_paneles": int(z.get("n_paneles") or 0)})

        p.sistema_fv = {
            "modo": "multizona",
            "zonas": zonas
        }

    else:
        sizing = sf_raw.get("sizing_input", {})

        p.sistema_fv = {
            "modo": sizing.get("modo"),
            "valor": float(sizing.get("valor", 0))
        }

    return p


# ==========================================================
# ZONAS (FIX: usar INPUT, no strings)
# ==========================================================
def _mostrar_zonas(ctx):

    st.markdown("### 🔀 Zonas FV (diseño real)")

    sf = getattr(ctx, "sistema_fv", {})
    zonas = sf.get("zonas", [])

    if not zonas:
        st.info("Sistema sin zonas definidas")
        return

    for i, z in enumerate(zonas, start=1):

        c1, c2 = st.columns(2)

        c1.metric(f"Zona {i}", z.get("n_paneles", 0))
        c2.metric("Strings (resultado)", "—")


# ==========================================================
# DETALLE COMPLETO
# ==========================================================
def _mostrar_detalle(paneles, electrical):

    st.markdown("## ⚡ Detalle eléctrico completo")

    panel = paneles.panel
    strings = paneles.strings
    corr = electrical.corrientes
    cond = electrical.conductores
    prot = electrical.protecciones

    # PANEL
    st.markdown("### 🔹 Panel")
    c1, c2, c3 = st.columns(3)
    c1.metric("Imp", f"{panel.imp_a:.2f} A")
    c2.metric("Isc", f"{panel.isc_a:.2f} A")
    c3.metric("I diseño", f"{corr.panel.i_diseno_a:.2f} A")

    # STRING
    st.markdown("### 🔗 Strings")

    data = []
    for i, s in enumerate(strings, 1):
        data.append({
            "String": f"S{i}",
            "Paneles": s.n_series,
            "Vmp": f"{s.vmp_string_v:.2f}",
            "Voc": f"{s.voc_frio_string_v:.2f}",
            "I": f"{s.imp_string_a:.2f}"
        })
    st.table(data)

    # MPPT
    st.markdown("### ⚡ MPPT")

    for i, m in enumerate(corr.mppt_detalle, 1):
        c1, c2 = st.columns(2)
        c1.metric(f"MPPT {i}", f"{m.i_operacion_a:.2f} A")
        c2.metric("Diseño", f"{m.i_diseno_a:.2f} A")

    # DC
    st.markdown("### 🔌 DC")
    c1, c2 = st.columns(2)
    c1.metric("I DC", f"{corr.dc_total.i_operacion_a:.2f} A")
    c2.metric("I diseño", f"{corr.dc_total.i_diseno_a:.2f} A")

    # AC
    st.markdown("### ⚡ AC")
    c1, c2 = st.columns(2)
    c1.metric("I AC", f"{corr.ac.i_operacion_a:.2f} A")
    c2.metric("I diseño", f"{corr.ac.i_diseno_a:.2f} A")

    # CONDUCTORES
    st.markdown("### 🧵 Conductores")

    tr = cond.tramos

    data = []
    if tr.dc:
        data.append({"Tramo": "DC", "Calibre": tr.dc.calibre, "VD %": f"{tr.dc.vd_pct:.2f}"})
    if tr.ac:
        data.append({"Tramo": "AC", "Calibre": tr.ac.calibre, "VD %": f"{tr.ac.vd_pct:.2f}"})

    st.table(data)

    # PROTECCIONES
    st.markdown("### ⚠ Protecciones")

    c1, c2, c3 = st.columns(3)
    c1.metric("Breaker AC", f"{prot.ocpd_ac.tamano_a} A")
    c2.metric("DC", f"{prot.ocpd_dc_array.tamano_a} A")

    fus = prot.fusible_string
    fus_val = fus.tamano_a if fus and fus.tamano_a else "No requerido"
    c3.metric("Fusible", fus_val)


# ==========================================================
# RENDER
# ==========================================================
def render(ctx):

    e = _asegurar_dict(ctx, "electrico")
    _ui_inputs_electricos(e)

    try:
        p = _datosproyecto_desde_ctx(ctx)
        deps = construir_dependencias()

        resultado = ejecutar_estudio(p, deps)

        ctx.resultado = resultado
        st.session_state["resultado"] = resultado

    except Exception:
        import traceback
        st.error(traceback.format_exc())
        return

    if not resultado:
        return

    if resultado.strings and resultado.electrical:
        _mostrar_zonas(ctx)  # ← FIX
        _mostrar_detalle(resultado.strings, resultado.electrical)


# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:

    resultado = getattr(ctx, "resultado", None) or st.session_state.get("resultado")

    if not resultado:
        return False, ["Debe generar ingeniería."]

    return True, []
