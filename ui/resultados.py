from __future__ import annotations

import copy
from typing import List, Tuple

import streamlit as st
import pandas as pd

from ui.state_helpers import is_result_stale
from ui.rutas import preparar_salida

from reportes.generar_pdf_profesional import generar_pdf_profesional
from reportes.imagenes import generar_artefactos


# ==========================================================
# VALIDACIÓN
# ==========================================================
def _validar_ctx(ctx) -> bool:

    if getattr(ctx, "resultado_proyecto", None) is None:
        st.error("Genere primero la ingeniería eléctrica (Paso 5).")
        return False

    if getattr(ctx, "datos_proyecto", None) is None:
        st.error("Faltan datos del proyecto.")
        return False

    return True


def _get_resultado_proyecto(ctx):
    rp = getattr(ctx, "resultado_proyecto", None)
    if rp is None:
        raise ValueError("resultado_proyecto inexistente")
    return rp


# ==========================================================
# TABLA STREAMLIT (SIN HTML)
# ==========================================================
def _tabla(titulo: str, data: dict):

    st.markdown(f"### {titulo}")

    df = pd.DataFrame({
        "Parámetro": list(data.keys()),
        "Valor": list(data.values())
    })

    st.dataframe(df, use_container_width=True, hide_index=True)


# ==========================================================
# DATOS DEL PROYECTO
# ==========================================================
def _render_datos_proyecto(ctx):

    d = ctx.datos_proyecto

    _tabla("📊 Datos del proyecto", {
        "Ubicación": getattr(d, "ubicacion", "—"),
        "Consumo anual": f"{getattr(d, 'consumo_anual_kwh', 0):,.0f} kWh",
        "Tarifa": f"L {getattr(d, 'tarifa', 0):.2f}/kWh",
    })


# ==========================================================
# DIMENSIONAMIENTO
# ==========================================================
def _render_dimensionamiento(rp):

    s = rp.sizing

    _tabla("⚡ Dimensionamiento", {
        "Paneles": s.n_paneles,
        "Potencia DC": f"{s.pdc_kw:.2f} kW",
        "Potencia AC": f"{s.kw_ac:.2f} kW",
        "Relación DC/AC": f"{s.dc_ac_ratio:.2f}",
    })


# ==========================================================
# EQUIPOS
# ==========================================================
def _render_equipos(rp):

    inv = rp.sizing.inversor

    _tabla("🔌 Inversor", {
        "Potencia": f"{inv.kw_ac} kW",
        "MPPT": inv.n_mppt,
        "Voltaje DC máximo": f"{inv.vdc_max_v} V",
        "Rango MPPT": f"{inv.mppt_min_v} - {inv.mppt_max_v} V",
    })


# ==========================================================
# CORRIENTES
# ==========================================================
def _render_corrientes(rp):

    e = rp.nec

    if not e or not e.ok:
        st.warning("Sin resultados eléctricos")
        return

    c = e.corrientes

    _tabla("⚡ Corrientes", {
        "Corriente string": f"{c.imp_string:.2f} A",
        "Corriente DC total": f"{c.idc_total:.2f} A",
        "Corriente AC": f"{c.iac:.2f} A",
    })


# ==========================================================
# CONDUCTORES
# ==========================================================
def _render_conductores(rp):

    e = rp.nec

    if not e or not e.ok:
        st.warning("Sin conductores")
        return

    cond = e.conductores

    if not cond or not cond.ok:
        st.warning("Conductores no disponibles")
        return

    t = cond.tramos[0]

    dc = getattr(t, "dc", None)
    ac = getattr(t, "ac", None)

    _tabla("🧵 Conductores DC", {
        "Calibre": getattr(dc, "calibre", "—") if dc else "—",
        "Ampacidad": f"{getattr(dc, 'ampacidad', '—')} A" if dc else "—",
    })

    _tabla("🧵 Conductores AC", {
        "Calibre": getattr(ac, "calibre", "—") if ac else "—",
        "Ampacidad": f"{getattr(ac, 'ampacidad', '—')} A" if ac else "—",
    })


# ==========================================================
# PROTECCIONES
# ==========================================================
def _render_protecciones(rp):

    e = rp.nec

    if not e or not e.ok:
        st.warning("Sin protecciones")
        return

    p = e.protecciones

    _tabla("⚠ Protecciones", {
        "Fusible string": f"{getattr(p, 'fusible_string', '—')} A",
        "Breaker AC": f"{getattr(p, 'breaker_ac', '—')} A",
    })


# ==========================================================
# PDF
# ==========================================================
def _ui_boton_pdf(disabled=False):

    st.markdown("### 📄 Generar propuesta")
    return st.button("Generar PDF", type="primary", disabled=disabled)


def _ejecutar_pipeline_pdf(ctx, rp):

    paths = preparar_salida("salidas")

    try:
        arte = generar_artefactos(
            res=rp,
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
            rp,
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


# ==========================================================
# RENDER
# ==========================================================
def render(ctx):

    st.markdown("## ⚡ Resultados del sistema FV")

    if not _validar_ctx(ctx):
        return

    rp = _get_resultado_proyecto(ctx)

    _render_datos_proyecto(ctx)
    _render_dimensionamiento(rp)
    _render_equipos(rp)
    _render_corrientes(rp)
    _render_conductores(rp)
    _render_protecciones(rp)

    stale = is_result_stale(ctx)

    if stale:
        st.warning("Resultados desactualizados")

    if not _ui_boton_pdf(disabled=stale):
        return

    _ejecutar_pipeline_pdf(ctx, copy.deepcopy(rp))


# ==========================================================
# VALIDAR
# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:

    errores = []

    if getattr(ctx, "resultado_proyecto", None) is None:
        errores.append("Debe ejecutar cálculo")

    if is_result_stale(ctx):
        errores.append("Resultados desactualizados")

    return (len(errores) == 0), errores
