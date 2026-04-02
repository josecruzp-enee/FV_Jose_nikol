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
# TABLA STREAMLIT
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

    consumo_anual = sum(getattr(d, "consumo_12m", []) or [])

    _tabla("📊 Datos del proyecto", {
        "Cliente": getattr(d, "cliente", "—"),
        "Ubicación": getattr(d, "ubicacion", "—"),
        "Consumo anual": f"{consumo_anual:,.0f} kWh",
        "Tarifa": f"L {getattr(d, 'tarifa_energia', 0):.2f}/kWh",
    })


# ==========================================================
# DIMENSIONAMIENTO
# ==========================================================
def _render_dimensionamiento(rp):

    s = rp.sizing

    _tabla("⚡ Sistema FV", {
        "Paneles": s.n_paneles,
        "Potencia instalada": f"{s.pdc_kw:.2f} kW",
        "Potencia inversor": f"{s.kw_ac:.2f} kW",
        "Relación DC/AC": f"{s.dc_ac_ratio:.2f}",
    })


# ==========================================================
# ENERGÍA
# ==========================================================
def _render_energia(rp):

    energia = getattr(rp, "energia", None)

    if not energia:
        st.warning("Sin datos de energía")
        return

    prod = sum(getattr(energia, "energia_12m", []) or [])
    cons = sum(getattr(rp, "consumo_12m", []) or [])

    cobertura = (prod / cons * 100) if cons > 0 else 0

    _tabla("⚡ Energía", {
        "Producción anual": f"{prod:,.0f} kWh",
        "Consumo anual": f"{cons:,.0f} kWh",
        "Cobertura": f"{cobertura:.1f} %",
    })


# ==========================================================
# FINANZAS
# ==========================================================
def _render_finanzas(rp):

    f = getattr(rp, "financiero", None)

    if not f:
        st.warning("Sin datos financieros")
        return

    _tabla("💰 Finanzas", {
        "Inversión": f"L {getattr(f, 'inversion_total', 0):,.0f}",
        "Ahorro anual": f"L {getattr(f, 'ahorro_anual', 0):,.0f}",
        "Payback": f"{getattr(f, 'payback', 0):.1f} años",
        "TIR": f"{getattr(f, 'tir', 0)*100:.1f} %",
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
    _render_energia(rp)
    _render_finanzas(rp)

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
