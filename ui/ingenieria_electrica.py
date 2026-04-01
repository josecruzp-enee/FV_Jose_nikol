import streamlit as st
import pandas as pd
import pprint

from core.aplicacion.dependencias import construir_dependencias
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.aplicacion.datos_proyecto import construir_datos_proyecto


# ==========================================================
# HELPERS
# ==========================================================
def _asegurar_dict(ctx, key):
    if not hasattr(ctx, key) or getattr(ctx, key) is None:
        setattr(ctx, key, {})
    return getattr(ctx, key)


# ==========================================================
# INPUTS
# ==========================================================
def _ui_inputs_electricos(e):

    st.markdown("## ⚙️ Parámetros eléctricos")

    col1, col2, col3 = st.columns(3)

    with col1:
        e["vac"] = st.number_input("Voltaje AC (V)", value=float(e.get("vac", 240)))

    with col2:
        e["fases"] = st.selectbox("Fases", [1, 3], index=0)

    with col3:
        e["fp"] = st.number_input("Factor de potencia", value=float(e.get("fp", 1.0)))

    st.markdown("### 📏 Distancias")

    col1, col2 = st.columns(2)

    with col1:
        e["dist_dc_m"] = st.number_input("Distancia DC (m)", value=float(e.get("15", 15)))

    with col2:
        e["dist_ac_m"] = st.number_input("Distancia AC (m)", value=float(e.get("25", 25)))


# ==========================================================
# RENDER RESULTADO
# ==========================================================
def _render_resultado(resultado):

    st.markdown("## ⚡ Resultado ingeniería")

    if resultado is None:
        st.error("Resultado es None")
        return

    # ======================================================
    # ESTADO
    # ======================================================
    st.markdown("### 🧪 Estado del sistema")

    estado = {
        "sizing": "OK" if resultado.sizing else "NULL",
        "paneles": "OK" if resultado.paneles else "NULL",
        "strings": "OK" if resultado.strings else "NULL",
        "energia": "OK" if resultado.energia else "NULL",
        "electrical": "OK" if resultado.electrical else "NULL",
        "finanzas": "OK" if resultado.financiero else "NULL",
    }

    st.json(estado)

    paneles = resultado.paneles
    electrical = resultado.electrical

    # ======================================================
    # STRINGS
    # ======================================================
    st.markdown("### 🔗 Strings FV")

    strings = paneles.strings if paneles else []

    if strings:
        data = []
        for i, s in enumerate(strings, 1):
            data.append([
                i, s.mppt, s.n_series,
                s.vmp_string_v, s.voc_frio_string_v,
                s.imp_string_a, s.isc_string_a
            ])

        df = pd.DataFrame(data, columns=[
            "#", "MPPT", "Series",
            "Vmp (V)", "Voc (V)", "Imp (A)", "Isc (A)"
        ])

        st.dataframe(df, width="stretch")
    else:
        st.warning("Sin strings")

    # ======================================================
    # ARRAY
    # ======================================================
    st.markdown("### ⚡ Array FV")

    if paneles and paneles.array:

        a = paneles.array

        col1, col2, col3 = st.columns(3)

        col1.metric("Potencia DC", f"{a.potencia_dc_w/1000:.2f} kW")
        col2.metric("Voltaje DC", f"{a.vdc_nom:.2f} V")
        col3.metric("Corriente DC", f"{a.idc_nom:.2f} A" if a.idc_nom else "—")

        col1.metric("Strings", a.n_strings_total)
        col2.metric("Paneles", a.n_paneles_total)
        col3.metric("MPPT", a.n_mppt)

    # ======================================================
    # CORRIENTES
    # ======================================================
    if electrical and hasattr(electrical, "corrientes"):

        st.markdown("### ⚡ Corrientes")

        c = electrical.corrientes

        df = pd.DataFrame([
            ["Panel", c.panel.i_operacion_a, c.panel.i_diseno_a],
            ["String", c.string.i_operacion_a, c.string.i_diseno_a],
            ["MPPT", c.mppt.i_operacion_a, c.mppt.i_diseno_a],
            ["DC Total", c.dc_total.i_operacion_a, c.dc_total.i_diseno_a],
            ["AC", c.ac.i_operacion_a, c.ac.i_diseno_a],
        ], columns=["Nivel", "I operación (A)", "I diseño (A)"])

        st.dataframe(df, width="stretch")

    # ======================================================
    # PROTECCIONES
    # ======================================================
    if electrical and hasattr(electrical, "protecciones"):

        st.markdown("### 🔌 Protecciones")

        p = electrical.protecciones

        df = pd.DataFrame([
            ["Breaker AC", p.ocpd_ac.tamano_a, p.ocpd_ac.norma],
            ["OCPD DC", p.ocpd_dc_array.tamano_a, p.ocpd_dc_array.norma],
            ["Fusible", "Sí" if p.fusible_string.requerido else "No", p.fusible_string.nota],
        ], columns=["Elemento", "Valor", "Norma"])

        st.dataframe(df, width="stretch")

    # ======================================================
    # CONDUCTORES
    # ======================================================
    if electrical and hasattr(electrical, "conductores"):

        st.markdown("### 🧵 Conductores")

        data = []

        for t in electrical.conductores.tramos.dc_mppt:
            data.append([
                t.nombre,
                t.calibre,
                t.material,
                t.i_diseno_a,
                t.vd_pct,
                "✔" if t.cumple else "❌"
            ])

        df = pd.DataFrame(data, columns=[
            "Tramo", "Calibre", "Material",
            "I diseño", "VD (%)", "Cumple"
        ])

        st.dataframe(df, width="stretch")

    # ======================================================
    # DEBUG (OPCIONAL)
    # ======================================================
    with st.expander("🧠 Debug completo"):
        st.code(pprint.pformat(resultado), language="python")


# ==========================================================
# MAIN
# ==========================================================
def render(ctx):

    st.markdown("# ⚡ Ingeniería eléctrica")

    e = _asegurar_dict(ctx, "electrico")
    _ui_inputs_electricos(e)

    if st.button("⚡ Generar ingeniería eléctrica"):

        try:
            p = construir_datos_proyecto(ctx)

            deps = construir_dependencias()
            resultado = ejecutar_estudio(p, deps)

            setattr(ctx, "resultado", resultado)

            st.success("✅ Ingeniería generada")

            _render_resultado(resultado)

        except Exception as ex:
            st.error("💥 Error")
            st.exception(ex)

    resultado = getattr(ctx, "resultado", None)

    if resultado:
        _render_resultado(resultado)


# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx):

    resultado = getattr(ctx, "resultado", None)

    if not resultado:
        return False, ["No se ha generado la ingeniería"]

    if not resultado.ok:
        return False, resultado.errores

    return True, []
