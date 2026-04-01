import streamlit as st
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
# RENDER RESULTADO
# ==========================================================
def _render_resultado(resultado):

    st.markdown("## ⚡ Resultado ingeniería")

    if resultado is None:
        st.error("Resultado es None")
        return

    # ======================================================
    # ESTADO CORREGIDO
    # ======================================================
    st.markdown("### 🧪 Estado del sistema")

    estado = {
        "sizing": "OK" if getattr(resultado, "sizing", None) else "NULL",
        "paneles": "OK" if getattr(resultado, "paneles", None) else "NULL",
        "strings": "OK" if getattr(resultado, "strings", None) else "NULL",
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
    # DEBUG PANELES (NUEVO)
    # ======================================================
    st.markdown("### 🔋 DEBUG PANELES")

    paneles = getattr(resultado, "paneles", None)

    if paneles:
        st.write(paneles)

        if hasattr(paneles, "array"):
            st.write("Array interno paneles:", paneles.array)
    else:
        st.warning("Paneles = None")

    # ======================================================
    # DEBUG ELECTRICAL
    # ======================================================
    st.markdown("### 🔎 DEBUG ELECTRICAL")

    electrical = getattr(resultado, "electrical", None)

    if electrical is None:
        st.warning("Electrical = None")
    else:
        try:
            st.write(electrical)

            if hasattr(electrical, "corrientes"):
                st.write("Corrientes:", electrical.corrientes)

            if hasattr(electrical, "conductores"):
                st.write("Conductores:", electrical.conductores)

            if hasattr(electrical, "protecciones"):
                st.write("Protecciones:", electrical.protecciones)

        except Exception as e:
            st.error(f"No se pudo mostrar detalle eléctrico: {e}")

    # ======================================================
    # STRINGS (CORREGIDO)
    # ======================================================
    st.markdown("### 🔗 Strings FV")

    strings = getattr(resultado, "strings", None)

    if isinstance(strings, list) and len(strings) > 0:
        for i, s in enumerate(strings, 1):
            st.write(
                f"String {i} | MPPT {s.mppt} | Series {s.n_series} | "
                f"Vmp {s.vmp_string_v:.2f} V | Voc {s.voc_frio_string_v:.2f} V | "
                f"Ip {s.imp_string_a:.2f} A | Isc {s.isc_string_a:.2f} A"
            )
    else:
        st.warning(f"Strings FV no definidos → {type(strings)}")

    # ======================================================
    # ARRAY FV
    # ======================================================
    st.markdown("### ⚡ Array FV")

    array = getattr(resultado, "array", None)

    if array:
        st.write(f"Potencia DC total: {array.potencia_dc_w/1000:.2f} kW")
        st.write(f"VDC nominal: {array.vdc_nom:.2f} V")
        st.write(f"Corriente DC nominal: {array.idc_nom}")
        st.write(f"Nº strings por MPPT: {array.strings_por_mppt}")
        st.write(f"Nº total de strings: {array.n_strings_total}")
        st.write(f"Nº total de paneles: {array.n_paneles_total}")
    else:
        st.info("Array FV no definido")

    # ======================================================
    # META
    # ======================================================
    st.markdown("### 📊 Meta")

    meta = getattr(resultado, "meta", None)

    if meta:
        st.write(f"Nº total de paneles: {meta.n_paneles_total}")
        st.write(f"Potencia DC total: {meta.pdc_kw:.2f} kW")
        st.write(f"Nº de inversores: {meta.n_inversores}")

    # ======================================================
    # DUMP COMPLETO (NUEVO 🔥)
    # ======================================================
    st.markdown("### 🧠 INSPECCIÓN COMPLETA")

    with st.expander("Resultado completo", expanded=False):
        st.code(pprint.pformat(resultado), language="python")

    if electrical:
        with st.expander("Electrical completo", expanded=False):
            st.code(pprint.pformat(electrical), language="python")


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
            p = construir_datos_proyecto(ctx)

            # ======================================================
            # DEBUG ENTRADA
            # ======================================================
            st.markdown("## 🧪 DEBUG INGENIERÍA")

            from dataclasses import asdict

            try:
                st.markdown("### 📦 Datosproyecto")
                st.json(asdict(p))
            except Exception:
                st.write(p)

            st.markdown("### ⚙️ Equipos")
            st.json(getattr(p, "equipos", {}))

            st.markdown("### ⚡ Eléctrico")
            st.json(getattr(p, "electrico", {}))

            st.markdown("### 🔗 Strings FV (entrada)")
            st.write(getattr(p, "strings", "No definido"))

            zonas = getattr(ctx, "zonas", None)
            if zonas:
                st.markdown("### 🧪 Multizona")
                st.json(zonas)

            # ======================================================
            # EJECUTAR
            # ======================================================
            deps = construir_dependencias()
            resultado = ejecutar_estudio(p, deps)

            setattr(ctx, "resultado", resultado)

            st.success("✅ Ingeniería generada")

            _render_resultado(resultado)

        except Exception as ex:
            st.error("💥 Error ejecutando ingeniería")
            st.exception(ex)
            return

    # ======================================================
    # MOSTRAR RESULTADO PREVIO
    # ======================================================
    try:
        resultado = getattr(ctx, "resultado", None)

        if resultado:
            _render_resultado(resultado)
        else:
            st.info("Aún no se ha generado resultado")

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
