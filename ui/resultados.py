from __future__ import annotations

from typing import List, Tuple

import pandas as pd
import streamlit as st

from ui.state_helpers import is_result_stale
from ui.rutas import preparar_salida

from reportes.generar_pdf_profesional import (
    generar_pdf_profesional,
)
from reportes.imagenes import generar_artefactos


PDF_SESSION_KEY = "pdf_fv_bytes"


# ==========================================================
# VALIDACIÓN
# ==========================================================

def _validar_ctx(ctx) -> bool:

    if getattr(ctx, "resultado_proyecto", None) is None:
        st.error(
            "Genere primero la ingeniería eléctrica (Paso 5)."
        )
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
# LECTURA DE DATOS
# ==========================================================

def _leer(objeto, campo, default=None):

    if objeto is None:
        return default

    if isinstance(objeto, dict):
        return objeto.get(campo, default)

    return getattr(objeto, campo, default)


# ==========================================================
# TABLA STREAMLIT
# ==========================================================

def _tabla(titulo: str, data: dict):

    st.markdown(f"### {titulo}")

    df = pd.DataFrame({
        "Parámetro": [
            str(valor)
            for valor in data.keys()
        ],
        "Valor": [
            str(valor)
            for valor in data.values()
        ],
    })

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )


# ==========================================================
# DATOS DEL PROYECTO
# ==========================================================

def _render_datos_proyecto(ctx):

    datos = ctx.datos_proyecto
    consumo_12m = (
        getattr(datos, "consumo_12m", [])
        or []
    )
    consumo_anual = sum(consumo_12m)

    _tabla(
        "📊 Datos del proyecto",
        {
            "Cliente": getattr(
                datos,
                "cliente",
                "—",
            ),
            "Ubicación": getattr(
                datos,
                "ubicacion",
                "—",
            ),
            "Consumo anual": (
                f"{consumo_anual:,.0f} kWh"
            ),
            "Tarifa": (
                f"L "
                f"{getattr(datos, 'tarifa_energia', 0):.2f}"
                f"/kWh"
            ),
        },
    )


# ==========================================================
# DIMENSIONAMIENTO
# ==========================================================

def _render_dimensionamiento(rp):

    sizing = rp.sizing

    _tabla(
        "⚡ Sistema FV",
        {
            "Paneles": sizing.n_paneles,
            "Potencia instalada": (
                f"{sizing.pdc_kw:.2f} kW"
            ),
            "Potencia inversor": (
                f"{sizing.kw_ac:.2f} kW"
            ),
            "Relación DC/AC": (
                f"{sizing.dc_ac_ratio:.2f}"
            ),
        },
    )


# ==========================================================
# ENERGÍA
# ==========================================================

def _render_energia(rp, datos):

    energia = getattr(rp, "energia", None)

    if energia is None:
        st.warning("Sin datos de energía")
        return

    produccion_anual = sum(
        getattr(
            energia,
            "energia_util_12m",
            [],
        )
        or []
    )

    consumo_anual = sum(
        getattr(
            datos,
            "consumo_12m",
            [],
        )
        or []
    )

    cobertura = (
        produccion_anual / consumo_anual * 100.0
        if consumo_anual > 0
        else 0.0
    )

    _tabla(
        "⚡ Energía",
        {
            "Producción anual": (
                f"{produccion_anual:,.0f} kWh"
            ),
            "Consumo anual": (
                f"{consumo_anual:,.0f} kWh"
            ),
            "Cobertura": (
                f"{cobertura:.1f} %"
            ),
        },
    )


# ==========================================================
# FINANZAS
# ==========================================================

def _render_finanzas(rp):

    financiero = getattr(rp, "financiero", None)

    if not financiero:
        st.warning("Sin datos financieros")
        return

    capex = float(
        _leer(
            financiero,
            "capex_total_L",
            _leer(financiero, "capex_L", 0.0),
        )
        or 0.0
    )

    ahorro_anual = float(
        _leer(
            financiero,
            "ahorro_anual_L",
            0.0,
        )
        or 0.0
    )

    payback = _leer(
        financiero,
        "payback_anios",
        None,
    )

    tir = float(
        _leer(
            financiero,
            "tir_pct",
            0.0,
        )
        or 0.0
    )

    payback_texto = (
        f"{float(payback):.1f} años"
        if payback is not None
        else "No disponible"
    )

    _tabla(
        "💰 Finanzas",
        {
            "Inversión": (
                f"L {capex:,.0f}"
            ),
            "Ahorro anual": (
                f"L {ahorro_anual:,.0f}"
            ),
            "Payback": payback_texto,
            "TIR": (
                f"{tir:.1f} %"
            ),
        },
    )


# ==========================================================
# BOTÓN PDF
# ==========================================================

def _ui_boton_pdf(disabled=False):

    st.markdown("### 📄 Generar propuesta")

    return st.button(
        "Generar PDF",
        type="primary",
        disabled=disabled,
    )


# ==========================================================
# ARTEFACTOS
# ==========================================================

def _generar_graficos_pdf(ctx, rp, paths):

    try:
        artefactos = generar_artefactos(
            res=rp,
            out_dir=paths.get(
                "out_dir",
                "salidas",
            ),
            proyecto=ctx.datos_proyecto,
            vista_resultados={},
            dos_aguas=True,
        )

        if isinstance(artefactos, dict):
            paths.update(artefactos)

    except Exception as error:
        st.warning(
            "No se pudieron generar algunos gráficos: "
            f"{error}"
        )


# ==========================================================
# GENERACIÓN DEL PDF
# ==========================================================

def _ejecutar_pipeline_pdf(ctx, rp) -> bytes:

    paths = preparar_salida("salidas")

    _generar_graficos_pdf(
        ctx,
        rp,
        paths,
    )

    datos_pdf = dict(
        getattr(
            ctx.datos_proyecto,
            "__dict__",
            {},
        )
    )

    pdf_path = generar_pdf_profesional(
        rp,
        datos_pdf,
        paths,
    )

    with open(pdf_path, "rb") as archivo:
        return archivo.read()


# ==========================================================
# DESCARGA
# ==========================================================

def _mostrar_descarga_pdf():

    pdf_bytes = st.session_state.get(
        PDF_SESSION_KEY
    )

    if not pdf_bytes:
        return

    st.download_button(
        "Descargar PDF",
        data=pdf_bytes,
        file_name="reporte_evaluacion_fv.pdf",
        mime="application/pdf",
        on_click="ignore",
    )


# ==========================================================
# RENDER
# ==========================================================

def render(ctx):

    st.markdown("## ⚡ Resultados del sistema FV")

    if not _validar_ctx(ctx):
        return

    rp = _get_resultado_proyecto(ctx)
    datos = ctx.datos_proyecto

    _render_datos_proyecto(ctx)
    _render_dimensionamiento(rp)
    _render_energia(rp, datos)
    _render_finanzas(rp)

    stale = is_result_stale(ctx)

    if stale:
        st.warning("Resultados desactualizados")
        st.session_state.pop(
            PDF_SESSION_KEY,
            None,
        )

    generar_pdf = _ui_boton_pdf(
        disabled=stale
    )

    if generar_pdf:
        try:
            with st.spinner(
                "Generando gráficos y PDF..."
            ):
                pdf_bytes = _ejecutar_pipeline_pdf(
                    ctx,
                    rp,
                )

                st.session_state[
                    PDF_SESSION_KEY
                ] = pdf_bytes

            st.success(
                "PDF generado correctamente."
            )

        except Exception as error:
            st.session_state.pop(
                PDF_SESSION_KEY,
                None,
            )
            st.exception(error)

    _mostrar_descarga_pdf()


# ==========================================================
# VALIDAR
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    errores: List[str] = []

    if getattr(
        ctx,
        "resultado_proyecto",
        None,
    ) is None:
        errores.append(
            "Debe ejecutar cálculo"
        )

    if is_result_stale(ctx):
        errores.append(
            "Resultados desactualizados"
        )

    return len(errores) == 0, errores
