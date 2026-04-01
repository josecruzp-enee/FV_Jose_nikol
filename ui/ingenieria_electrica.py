import streamlit as st

from core.aplicacion.dependencias import construir_dependencias
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.dominio.modelo import Datosproyecto


# ==========================================================
# HELPERS
# ==========================================================

def _asegurar_dict(ctx, key):
    if not hasattr(ctx, key) or getattr(ctx, key) is None:
        setattr(ctx, key, {})
    return getattr(ctx, key)


# ==========================================================
# INPUTS UI
# ==========================================================

def _ui_inputs_electricos(e):

    st.markdown("## ⚙️ Parámetros eléctricos")

    col1, col2, col3 = st.columns(3)

    with col1:
        e["vac"] = st.number_input(
            "Voltaje AC (V)",
            value=float(e.get("vac", 240)),
        )

    with col2:
        e["fases"] = st.selectbox(
            "Fases",
            options=[1, 3],
            index=0 if e.get("fases", 1) == 1 else 1,
        )

    with col3:
        e["fp"] = st.number_input(
            "Factor de potencia",
            value=float(e.get("fp", 1.0)),
        )

    st.markdown("### 📏 Distancias")

    col1, col2 = st.columns(2)

    with col1:
        e["dist_dc_m"] = st.number_input(
            "Distancia DC (m)",
            value=float(e.get("dist_dc_m", 15)),
        )

    with col2:
        e["dist_ac_m"] = st.number_input(
            "Distancia AC (m)",
            value=float(e.get("dist_ac_m", 25)),
        )


# ==========================================================
# CONVERSIÓN CTX → MODELO
# ==========================================================

def _datosproyecto_desde_ctx(ctx):

    p = Datosproyecto()

    # 🔹 copiar atributos existentes
    for attr in dir(ctx):
        if not attr.startswith("_"):
            try:
                setattr(p, attr, getattr(ctx, attr))
            except:
                pass

    # 🔹 asegurar estructura eléctrica
    e = _asegurar_dict(ctx, "electrico")

    p.electrico = {
        "vac": float(e.get("vac", 0)),
        "fases": int(e.get("fases", 1)),
        "fp": float(e.get("fp", 1.0)),
        "dist_dc_m": float(e.get("dist_dc_m", 0)),
        "dist_ac_m": float(e.get("dist_ac_m", 0)),
    }

    return p


# ==========================================================
# RENDER RESULTADO
# ==========================================================

def _render_resultado(resultado):

    st.markdown("## ⚡ Resultado ingeniería")

    if resultado is None:
        st.error("Resultado es None")
        return

    # ======================================================
    # ESTADO GENERAL
    # ======================================================
    st.markdown("### 🧪 Estado del sistema")

    estado = {
        "sizing": "OK" if resultado.sizing else "NULL",
        "paneles": "OK" if resultado.paneles else "NULL",
        "energia": "OK" if resultado.energia else "NULL",
        "electrical": "OK" if resultado.electrical else "NULL",
        "finanzas": "OK" if resultado.financiero else "NULL",
    }

    st.json(estado)

    # ======================================================
    # ERRORES
    # ======================================================
    if not getattr(resultado, "ok", True):
        st.error("❌ Proyecto con errores")

        if hasattr(resultado, "errores"):
            for err in resultado.errores:
                st.error(err)

    # ======================================================
    # DEBUG ELECTRICAL
    # ======================================================
    st.markdown("### 🔎 DEBUG ELECTRICAL")

    electrical = resultado.electrical

    if electrical is None:
        st.warning("Electrical = None")
        return

    try:
        st.write(electrical)
    except Exception as e:
        st.error(f"No se pudo mostrar electrical: {e}")

    # ======================================================
    # DETALLE BÁSICO
    # ======================================================
    st.markdown("### 📊 Datos básicos")

    try:
        if hasattr(electrical, "corrientes"):
            st.write("Corrientes:", electrical.corrientes)

        if hasattr(electrical, "conductores"):
            st.write("Conductores:", electrical.conductores)

        if hasattr(electrical, "protecciones"):
            st.write("Protecciones:", electrical.protecciones)

    except Exception as e:
        st.error(f"Error mostrando detalle: {e}")


# ==========================================================
# MAIN RENDER
# ==========================================================

def render(ctx):

    st.markdown("# ⚡ Ingeniería eléctrica")

    # ======================================================
    # INPUTS
    # ======================================================
    e = _asegurar_dict(ctx, "electrico")
    _ui_inputs_electricos(e)

    # ======================================================
    # BOTÓN
    # ======================================================
    if st.button("⚡ Generar ingeniería eléctrica"):

        try:
            # 🔹 construir proyecto
            p = _datosproyecto_desde_ctx(ctx)

            # 🔹 dependencias
            deps = construir_dependencias()

            # 🔹 ejecutar flujo completo
            resultado = ejecutar_estudio(p, deps)

            # 🔥 GUARDAR EN CONTEXTO
            setattr(ctx, "resultado", resultado)

            st.success("✅ Ingeniería generada")

        except Exception as ex:
            st.error("💥 Error ejecutando ingeniería")
            st.exception(ex)
            return

    # ======================================================
    # MOSTRAR RESULTADO
    # ======================================================
    resultado = getattr(ctx, "resultado", None)

    if resultado:
        _render_resultado(resultado)


def validar(ctx):

    resultado = getattr(ctx, "resultado", None)

    if not resultado:
        return False

    return True
