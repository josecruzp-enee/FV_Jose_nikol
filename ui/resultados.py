# ui/resultados.py
from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

import streamlit as st

from ui.state_helpers import is_result_stale
from core.result_accessors import (
    get_sizing,
    get_kwp_dc,
)
from core.rutas import money_L, num
from reportes.generar_pdf_profesional import generar_pdf_profesional
from reportes.imagenes import generar_artefactos
from core.rutas import preparar_salida


# ==========================================================
# Validaciones básicas
# ==========================================================
def _validar_ctx(ctx) -> bool:
    if getattr(ctx, "resultado_proyecto", None) is None:
        st.error("No hay resultados del estudio. Genere primero la ingeniería eléctrica (Paso 5).")
        return False
    if not hasattr(ctx, "datos_proyecto") or ctx.datos_proyecto is None:
        st.error("Falta ctx.datos_proyecto. En Paso 5 debes guardar Datosproyecto en ctx.datos_proyecto.")
        return False
    return True


def _get_resultado_proyecto(ctx) -> dict:
    rp = getattr(ctx, "resultado_proyecto", None) or {}
    return rp if isinstance(rp, dict) else {}


# ==========================================================
# KPIs
# ==========================================================
def _render_kpis(resultado_proyecto: dict) -> None:
    tecnico = resultado_proyecto.get("tecnico") or {}
    financiero = resultado_proyecto.get("financiero") or {}

    sizing = tecnico.get("sizing") or {}

    kwp_dc = get_kwp_dc({"sizing": dict(sizing or {})})
    cuota = float(financiero.get("cuota_mensual") or 0.0)
    evaluacion = financiero.get("evaluacion") or {}
    estado = str(evaluacion.get("estado") or evaluacion.get("dictamen") or "N/D")

    c1, c2, c3 = st.columns(3)
    c1.metric("Sistema (kWp DC)", num(kwp_dc, 2))
    c2.metric("Cuota mensual", money_L(cuota))
    c3.metric("Estado", estado)

    if kwp_dc <= 0:
        st.warning("Sizing incompleto.")


# ==========================================================
# NEC resumen
# ==========================================================
def _render_nec_resumen(resultado_proyecto: dict) -> None:
    st.subheader("Ingeniería eléctrica (NEC 2023)")

    tecnico = resultado_proyecto.get("tecnico") or {}
    nec = tecnico.get("electrico_nec") or {}

    # wrapper nuevo
    if isinstance(nec, dict) and "paq" in nec:
        paq = nec.get("paq") or {}
    else:
        paq = nec or {}

    if not paq:
        st.info("Sin paquete NEC disponible.")
        return

    dc = paq.get("dc") or {}
    ac = paq.get("ac") or {}
    ocpd = paq.get("ocpd") or {}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Strings", str(dc.get("n_strings", "—")))
    c2.metric("I DC diseño", f"{dc.get('i_array_design_a','—')} A")
    c3.metric("I AC diseño", f"{ac.get('i_ac_design_a','—')} A")
    br = (ocpd.get("breaker_ac") or {})
    c4.metric("Breaker AC", f"{br.get('tamano_a','—')} A")

    with st.expander("Ver paquete NEC (crudo)", expanded=False):
        st.json(paq)


# ==========================================================
# PDF Pipeline
# ==========================================================
def _ui_boton_pdf(disabled: bool = False) -> bool:
    st.markdown("#### Generar propuesta (PDF)")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        run = st.button("Generar PDF", type="primary", disabled=disabled)
    with col_b:
        st.caption("Genera charts, layout y PDF profesional usando los datos ya calculados.")
    return bool(run)


def _ejecutar_pipeline_pdf(ctx, resultado_proyecto: dict) -> None:
    paths = preparar_salida("salidas")

    out_dir = paths.get("out_dir") or paths.get("base_dir") or "salidas"

    # Generar artefactos (charts + layout)
    try:
        arte = generar_artefactos(
            res=resultado_proyecto,  # ahora pasamos estructura moderna
            out_dir=out_dir,
            vista_resultados={},
            dos_aguas=True,
        )
        paths.update(arte)
    except Exception as e:
        st.exception(e)
        st.warning("No se pudieron generar artefactos (charts/layout). Se intentará generar el PDF igual.")

    # Generar PDF
    try:
        datos_pdf = dict(getattr(ctx.datos_proyecto, "__dict__", {}))
        pdf_path = generar_pdf_profesional(resultado_proyecto, datos_pdf, paths)

        with open(pdf_path, "rb") as f:
            st.download_button(
                "Descargar PDF",
                data=f,
                file_name="reporte_evaluacion_fv.pdf",
                mime="application/pdf",
            )

        st.success("PDF generado.")

    except Exception as e:
        st.exception(e)
        st.warning("No se pudo generar PDF.")


# ==========================================================
# Paso 6
# ==========================================================
def render(ctx) -> None:
    st.markdown("### Resultados y propuesta")

    if not _validar_ctx(ctx):
        return

    resultado_proyecto = _get_resultado_proyecto(ctx)

    _render_kpis(resultado_proyecto)
    st.divider()

    _render_nec_resumen(resultado_proyecto)
    st.divider()

    stale_inputs = is_result_stale(ctx)
    if stale_inputs:
        st.warning("Los datos de entrada cambiaron después del cálculo del Paso 5. Regenera la ingeniería antes del PDF.")

    if not _ui_boton_pdf(disabled=stale_inputs):
        return

    _ejecutar_pipeline_pdf(ctx, copy.deepcopy(resultado_proyecto))


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []

    if getattr(ctx, "resultado_proyecto", None) is None:
        errores.append("No hay resultados del estudio (genere en Paso 5).")

    if is_result_stale(ctx):
        errores.append("Los resultados están desactualizados. Regenera la ingeniería del Paso 5.")

    return (len(errores) == 0), errores
