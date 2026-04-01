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

    # ======================================================
    # CREAR OBJETO BASE (SIN ELÉCTRICO)
    # ======================================================
    p = Datosproyecto(

        # -------------------------------
        # DATOS GENERALES
        # -------------------------------
        cliente=getattr(ctx, "cliente", ""),
        ubicacion=getattr(ctx, "ubicacion", ""),
        lat=float(getattr(ctx, "lat", 0)),
        lon=float(getattr(ctx, "lon", 0)),

        # -------------------------------
        # CONSUMO
        # -------------------------------
        consumo_12m=getattr(ctx, "consumo_12m", [0]*12),

        # -------------------------------
        # TARIFA
        # -------------------------------
        tarifa_energia=float(getattr(ctx, "tarifa_energia", 0)),
        cargos_fijos=float(getattr(ctx, "cargos_fijos", 0)),

        # -------------------------------
        # PRODUCCIÓN FV
        # -------------------------------
        prod_base_kwh_kwp_mes=getattr(ctx, "prod_base_kwh_kwp_mes", [0]*12),
        factores_fv_12m=getattr(ctx, "factores_fv_12m", [1]*12),

        # -------------------------------
        # OBJETIVO
        # -------------------------------
        cobertura_objetivo=float(getattr(ctx, "cobertura_objetivo", 1.0)),

        # -------------------------------
        # COSTOS
        # -------------------------------
        costo_usd_kwp=float(getattr(ctx, "costo_usd_kwp", 1000)),
        tcambio=float(getattr(ctx, "tcambio", 24.5)),
        tasa_anual=float(getattr(ctx, "tasa_anual", 0.1)),
        plazo_anios=int(getattr(ctx, "plazo_anios", 10)),
        porcentaje_financiado=float(getattr(ctx, "porcentaje_financiado", 0)),
    )

    # ======================================================
    # ASIGNAR BLOQUE ELÉCTRICO (FUERA DEL CONSTRUCTOR)
    # ======================================================
    e = _asegurar_dict(ctx, "electrico")

    p.electrico = {
        "vac": float(e.get("vac", 240)),
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
    # ESTADO GENERAL (BLINDADO)
    # ======================================================
    st.markdown("### 🧪 Estado del sistema")

    estado = {
        "sizing": "OK" if getattr(resultado, "sizing", None) else "NULL",
        "paneles": "OK" if getattr(resultado, "strings", None) else "NULL",
        "energia": "OK" if getattr(resultado, "energia", None) else "NULL",
        "electrical": "OK" if getattr(resultado, "electrical", None) else "NULL",
        "finanzas": "OK" if getattr(resultado, "financiero", None) else "NULL",
    }

    st.json(estado)

    # ======================================================
    # ERRORES
    # ======================================================
    if not getattr(resultado, "ok", True):
        st.error("❌ Proyecto con errores")

        for err in getattr(resultado, "errores", []):
            st.error(err)

    # ======================================================
    # DEBUG ELECTRICAL
    # ======================================================
    st.markdown("### 🔎 DEBUG ELECTRICAL")

    electrical = getattr(resultado, "electrical", None)

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
            # ==============================================
            # CONSTRUIR PROYECTO
            # ==============================================
            p = _datosproyecto_desde_ctx(ctx)

            # ======================================================
            # DEBUG COMPLETO (INGENIERÍA REAL)
            # ======================================================
            st.markdown("## 🧪 DEBUG INGENIERÍA")

            from dataclasses import asdict

            # INPUT COMPLETO
            try:
                st.markdown("### 📦 Datosproyecto")
                st.json(asdict(p))
            except Exception:
                st.write(p)

            # EQUIPOS
            st.markdown("### ⚙️ Equipos")
            st.json(getattr(p, "equipos", {}))

            # ELÉCTRICO
            st.markdown("### ⚡ Eléctrico")
            st.json(getattr(p, "electrico", {}))

            # STRINGS (si existe)
            st.markdown("### 🔗 Strings FV")
            st.write(getattr(p, "strings", "No definido"))

            # MULTIZONA
            zonas = getattr(ctx, "zonas", None)
            if zonas:
                st.markdown("### 🧪 Multizona")
                st.json(zonas)

            # ==============================================
            # EJECUTAR MOTOR
            # ==============================================
            deps = construir_dependencias()
            resultado = ejecutar_estudio(p, deps)

            # GUARDAR RESULTADO
            setattr(ctx, "resultado", resultado)

            st.success("✅ Ingeniería generada")

        except Exception as ex:
            st.error("💥 Error ejecutando ingeniería")
            st.exception(ex)
            return

    # ======================================================
    # MOSTRAR RESULTADO
    # ======================================================
    try:
        resultado = getattr(ctx, "resultado", None)

        if resultado is None:
            st.info("Aún no se ha generado resultado")
            return

        # ==================================================
        # ESTADO
        # ==================================================
        st.markdown("## 🧪 Estado del sistema")

        estado = {
            "sizing": "OK" if getattr(resultado, "sizing", None) else "NULL",
            "paneles": "OK" if getattr(resultado, "strings", None) else "NULL",
            "energia": "OK" if getattr(resultado, "energia", None) else "NULL",
            "electrical": "OK" if getattr(resultado, "electrical", None) else "NULL",
            "finanzas": "OK" if getattr(resultado, "financiero", None) else "NULL",
        }

        st.json(estado)

        # ==================================================
        # ERRORES
        # ==================================================
        if not getattr(resultado, "ok", True):
            st.error("❌ Proyecto con errores")

            for err in getattr(resultado, "errores", []):
                st.error(err)

        # ==================================================
        # DEBUG ELECTRICAL
        # ==================================================
        st.markdown("## 🔎 DEBUG ELECTRICAL")

        electrical = getattr(resultado, "electrical", None)

        if electrical is None:
            st.warning("Electrical = None")
            return

        st.write(electrical)

        # ==================================================
        # DETALLE BÁSICO
        # ==================================================
        st.markdown("## 📊 Detalle eléctrico")

        if hasattr(electrical, "corrientes"):
            st.write("Corrientes:", electrical.corrientes)

        if hasattr(electrical, "conductores"):
            st.write("Conductores:", electrical.conductores)

        if hasattr(electrical, "protecciones"):
            st.write("Protecciones:", electrical.protecciones)

    except Exception as e:
        st.error("Error renderizando resultado")
        st.exception(e)

# ==========================================================
# VALIDACIÓN
# ==========================================================

def validar(ctx):

    resultado = getattr(ctx, "resultado", None)

    if not resultado:
        return False, ["No se ha generado la ingeniería"]

    if not getattr(resultado, "ok", True):
        return False, getattr(resultado, "errores", ["Error desconocido"])

    return True, []
