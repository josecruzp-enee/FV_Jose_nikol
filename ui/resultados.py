from __future__ import annotations

"""
PASO 6 — RESULTADOS Y PROPUESTA
FV Engine (UI limpia profesional)
"""

import copy
from typing import List, Tuple

import streamlit as st

from ui.state_helpers import is_result_stale
from ui.rutas import money_L, num, preparar_salida

from reportes.generar_pdf_profesional import generar_pdf_profesional
from reportes.imagenes import generar_artefactos


# ==========================================================
# VALIDACIÓN CONTEXTO
# ==========================================================
def _validar_ctx(ctx) -> bool:

    if getattr(ctx, "resultado_proyecto", None) is None:
        st.error("Genere primero la ingeniería eléctrica (Paso 5).")
        return False

    if getattr(ctx, "datos_proyecto", None) is None:
        st.error("Faltan datos del proyecto.")
        return False

    return True


# ==========================================================
# RESULTADO
# ==========================================================
def _get_resultado_proyecto(ctx):
    rp = getattr(ctx, "resultado_proyecto", None)
    if rp is None:
        raise ValueError("resultado_proyecto inexistente")
    return rp


# ==========================================================
# BLOQUE 1 — DATOS DEL PROYECTO
# ==========================================================
def _render_datos_proyecto(ctx) -> None:

    st.subheader("Datos del proyecto")

    datos = getattr(ctx, "datos_proyecto", None)

    col1, col2, col3 = st.columns(3)

    col1.metric("Ubicación", getattr(datos, "ubicacion", "—"))
    col2.metric(
        "Consumo anual",
        f"{getattr(datos, 'consumo_anual_kwh', 0):,.0f} kWh"
    )
    col3.metric(
        "Tarifa",
        f"L {getattr(datos, 'tarifa', 0):.2f}/kWh"
    )


# ==========================================================
# BLOQUE 2 — DIMENSIONAMIENTO
# ==========================================================
def _render_dimensionamiento(rp) -> None:

    st.subheader("Dimensionamiento del sistema")

    sizing = getattr(rp, "sizing", None)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Paneles", getattr(sizing, "n_paneles", 0))
    c2.metric("Potencia DC", f"{getattr(sizing, 'pdc_kw', 0):.2f} kW")
    c3.metric("Potencia AC", f"{getattr(sizing, 'kw_ac', 0):.2f} kW")
    c4.metric("DC/AC", f"{getattr(sizing, 'dc_ac_ratio', 0):.2f}")


# ==========================================================
# BLOQUE 3 — EQUIPOS
# ==========================================================
def _render_equipos(rp) -> None:

    st.subheader("Equipos del sistema")

    sizing = getattr(rp, "sizing", None)
    inv = getattr(sizing, "inversor", None)

    col1, col2 = st.columns(2)

    col1.write("**Inversor**")
    col1.write(f"Potencia: {getattr(inv, 'kw_ac', 0)} kW")
    col1.write(f"MPPT: {getattr(inv, 'n_mppt', 0)}")

    col2.write("**Parámetros eléctricos**")
    col2.write(f"Vdc máx: {getattr(inv, 'vdc_max_v', 0)} V")
    col2.write(
        f"Rango MPPT: {getattr(inv, 'mppt_min_v', 0)} - "
        f"{getattr(inv, 'mppt_max_v', 0)} V"
    )


# ==========================================================
# BLOQUE 4 — CORRIENTES
# ==========================================================
def _render_corrientes(rp) -> None:

    st.subheader("Corrientes del sistema")

    electrical = getattr(rp, "nec", None)

    if not electrical or not getattr(electrical, "ok", False):
        st.warning("Sin resultados eléctricos")
        return

    corr = getattr(electrical, "corrientes", {}) or {}

    c1, c2, c3 = st.columns(3)

    c1.metric("I string", f"{corr.get('string', 0):.2f} A")
    c2.metric("I DC total", f"{corr.get('idc_total', 0):.2f} A")
    c3.metric("I AC", f"{corr.get('iac', 0):.2f} A")


# ==========================================================
# BLOQUE 5 — CONDUCTORES
# ==========================================================
def _render_conductores(rp) -> None:

    st.subheader("Conductores")

    electrical = getattr(rp, "nec", None)

    cond = getattr(electrical, "conductores", {}) or {}

    dc = cond.get("dc", {})
    ac = cond.get("ac", {})

    c1, c2 = st.columns(2)

    c1.metric("Conductor DC", dc.get("calibre", "—"))
    c1.write(f"Ampacidad: {dc.get('ampacidad', '—')} A")

    c2.metric("Conductor AC", ac.get("calibre", "—"))
    c2.write(f"Ampacidad: {ac.get('ampacidad', '—')} A")


# ==========================================================
# BLOQUE 6 — PROTECCIONES
# ==========================================================
def _render_protecciones(rp) -> None:

    st.subheader("Protecciones")

    electrical = getattr(rp, "nec", None)

    prot = getattr(electrical, "protecciones", {}) or {}

    c1, c2 = st.columns(2)

    c1.metric("Fusible string", f"{prot.get('fusible_string', '—')} A")
    c2.metric("Breaker AC", f"{prot.get('breaker_ac', '—')} A")


# ==========================================================
# BOTÓN PDF
# ==========================================================
def _ui_boton_pdf(disabled: bool = False) -> bool:

    st.markdown("#### Generar propuesta (PDF)")

    col_a, col_b = st.columns([1, 2])

    with col_a:
        run = st.button("Generar PDF", type="primary", disabled=disabled)

    with col_b:
        st.caption("Genera PDF profesional del proyecto")

    return bool(run)


# ==========================================================
# PIPELINE PDF
# ==========================================================
def _ejecutar_pipeline_pdf(ctx, resultado_proyecto) -> None:

    paths = preparar_salida("salidas")

    try:
        arte = generar_artefactos(
            res=resultado_proyecto,
            out_dir=paths.get("out_dir", "salidas"),
            vista_resultados={},
            dos_aguas=True,
        )
        paths.update(arte)
    except Exception:
        st.warning("No se pudieron generar gráficos")

    try:
        datos_pdf = dict(getattr(ctx.datos_proyecto, "__dict__", {}))

        pdf_path = generar_pdf_profesional(
            resultado_proyecto,
            datos_pdf,
            paths,
        )

        with open(pdf_path, "rb") as f:
            st.download_button(
                "Descargar PDF",
                data=f,
                file_name="reporte_evaluacion_fv.pdf",
                mime="application/pdf",
            )

        st.success("PDF generado")

    except Exception as e:
        st.exception(e)
        st.error("Error generando PDF")


# ==========================================================
# RENDER PRINCIPAL
# ==========================================================
def render(ctx) -> None:

    st.markdown("### Resultados del sistema FV")

    if not _validar_ctx(ctx):
        return

    rp = _get_resultado_proyecto(ctx)

    _render_datos_proyecto(ctx)
    st.divider()

    _render_dimensionamiento(rp)
    st.divider()

    _render_equipos(rp)
    st.divider()

    _render_corrientes(rp)
    st.divider()

    _render_conductores(rp)
    st.divider()

    _render_protecciones(rp)
    st.divider()

    stale = is_result_stale(ctx)

    if stale:
        st.warning("Resultados desactualizados. Recalcular.")

    if not _ui_boton_pdf(disabled=stale):
        return

    _ejecutar_pipeline_pdf(ctx, copy.deepcopy(rp))


# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:

    errores: List[str] = []

    if getattr(ctx, "resultado_proyecto", None) is None:
        errores.append("Debe ejecutar el cálculo primero.")

    if is_result_stale(ctx):
        errores.append("Resultados desactualizados.")

    return (len(errores) == 0), errores
