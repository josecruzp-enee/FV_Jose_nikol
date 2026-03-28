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

    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),
        consumo_12m=[float(x) for x in c.get("consumo_12m", [0]*12)],
        instalacion_electrica=InstalacionElectrica(
            vac=float(e.get("vac", 240)),
            fases=int(e.get("fases", 1)),
            fp=float(e.get("fp", 1.0)),
            dist_dc_m=float(e.get("dist_dc_m", 15)),
            dist_ac_m=float(e.get("dist_ac_m", 25)),
        )
    )

    p.equipos = Equipos(
        panel_id=eq.get("panel_id"),
        inversor_id=eq.get("inversor_id"),
    )

    # MULTIZONA
    if sf_raw.get("usar_zonas"):
        zonas = [{"n_paneles": int(z.get("n_paneles") or 0)} for z in sf_raw.get("zonas", [])]
        p.sistema_fv = {"modo": "multizona", "zonas": zonas}
    else:
        sizing = sf_raw.get("sizing_input", {})
        p.sistema_fv = {
            "modo": sizing.get("modo"),
            "valor": float(sizing.get("valor"))
        }

    return p


# ==========================================================
# ZONAS
# ==========================================================
def _mostrar_zonas(paneles):

    st.markdown("### 🔀 Zonas FV (diseño real)")

    strings = paneles.strings

    zonas = {}

    for s in strings:
        n = s.n_series
        if n not in zonas:
            zonas[n] = {"n_paneles": 0, "n_strings": 0}
        zonas[n]["n_paneles"] += n
        zonas[n]["n_strings"] += 1

    for i, (_, d) in enumerate(zonas.items(), start=1):
        st.markdown(f"#### Zona {i}")
        c1, c2 = st.columns(2)
        c1.metric("Paneles", d["n_paneles"])
        c2.metric("Strings", d["n_strings"])


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
            "String": i,
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
    c3.metric("Fusible", f"{prot.fusible_string.tamano_a} A")


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
        _mostrar_zonas(resultado.strings)
        _mostrar_detalle(resultado.strings, resultado.electrical)


# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:

    resultado = getattr(ctx, "resultado", None) or st.session_state.get("resultado")

    if not resultado:
        return False, ["Debe generar ingeniería."]

    return True, []
