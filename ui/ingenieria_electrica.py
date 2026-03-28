from __future__ import annotations

from typing import List, Tuple
import streamlit as st

from core.dominio.modelo import Datosproyecto, InstalacionElectrica, Equipos
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.aplicacion.dependencias import construir_dependencias

from ui.state_helpers import ensure_dict


# ==========================================================
# UTILIDADES
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

        zonas = []
        for z in sf_raw.get("zonas", []):
            zonas.append({"n_paneles": int(z.get("n_paneles") or 0)})

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
def _mostrar_zonas(paneles, corrientes):

    st.markdown("### 🔀 Zonas FV (reales)")

    strings = getattr(paneles, "strings", [])

    zonas = {}

    for s in strings:
        n = s.n_series
        if n not in zonas:
            zonas[n] = {"n_paneles": 0, "n_strings": 0}
        zonas[n]["n_paneles"] += n
        zonas[n]["n_strings"] += 1

    for i, (n, d) in enumerate(zonas.items(), start=1):
        st.markdown(f"#### Zona {i}")
        c1, c2 = st.columns(2)
        c1.metric("Paneles", d["n_paneles"])
        c2.metric("Strings", d["n_strings"])


# ==========================================================
# DETALLE COMPLETO
# ==========================================================
def _mostrar_detalle(paneles, electrical):

    st.markdown("## ⚡ Detalle eléctrico completo")

    strings = paneles.strings
    panel = paneles.panel
    corr = electrical.corrientes

    # PANEL
    st.markdown("### 🔹 Panel")
    st.write(f"Imp: {panel.imp_a:.2f} A")
    st.write(f"Isc: {panel.isc_a:.2f} A")
    st.write(f"I diseño: {corr.panel.i_diseno_a:.2f} A")

    # STRING
    st.markdown("### 🔗 Strings")
    for i, s in enumerate(strings, 1):
        st.write(f"String {i}: {s.n_series} paneles → {s.imp_string_a:.2f} A")

    # MPPT
    st.markdown("### ⚡ MPPT")
    for i, m in enumerate(corr.mppt_detalle, 1):
        st.write(f"MPPT {i}: {m.i_diseno_a:.2f} A")

    # DC
    st.markdown("### 🔌 DC")
    st.write(f"Total DC: {corr.dc_total.i_diseno_a:.2f} A")

    # AC
    st.markdown("### ⚡ AC")
    st.write(f"AC: {corr.ac.i_diseno_a:.2f} A")


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

    # ZONAS
    if resultado.strings and resultado.electrical:
        _mostrar_zonas(resultado.strings, resultado.electrical.corrientes)

    # DETALLE COMPLETO
    if resultado.strings and resultado.electrical:
        _mostrar_detalle(resultado.strings, resultado.electrical)


# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:

    resultado = getattr(ctx, "resultado", None) or st.session_state.get("resultado")

    if not resultado:
        return False, ["Debe generar ingeniería."]

    return True, []
