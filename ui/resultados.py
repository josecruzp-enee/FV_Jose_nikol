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

    # 🔥 calcular consumo anual correctamente
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
# CORRIENTES (🔥 CORREGIDO)
# ==========================================================
def _render_corrientes(rp):

    e = getattr(rp, "electrical", None)

    if e is None:
        st.warning("Sin resultados eléctricos")
        return

    c = getattr(e, "corrientes", None)

    if not c or not getattr(c, "ok", False):
        st.warning("Corrientes no disponibles")
        return

    _tabla("⚡ Corrientes", {
        "Corriente string": f"{getattr(c.string, 'i_operacion_a', 0):.2f} A",
        "Corriente DC total": f"{getattr(c.dc_total, 'i_operacion_a', 0):.2f} A",
        "Corriente AC": f"{getattr(c.ac, 'i_operacion_a', 0):.2f} A",
    })

# ==========================================================
# CONDUCTORES (🔥 CORREGIDO)
# ==========================================================
def _render_conductores(rp):

    e = getattr(rp, "electrical", None)

    if e is None:
        st.warning("Sin conductores")
        return

    cond = getattr(e, "conductores", None)

    if not cond or not getattr(cond, "ok", False):
        st.warning("Conductores no disponibles")
        return

    t = cond.tramos  # 🔥 FIX

    dc = getattr(t, "dc", None)
    ac = getattr(t, "ac", None)

    # -----------------------------
    # DC GLOBAL
    # -----------------------------
    if dc:
        _tabla("🧵 DC Global", {
            "Calibre": dc.calibre,
            "Ampacidad": f"{dc.ampacidad_ajustada_a} A",
        })

    # -----------------------------
    # MPPT (NUEVO)
    # -----------------------------
    if hasattr(t, "mppt") and t.mppt:

        for i, m in enumerate(t.mppt):
            _tabla(f"🔌 MPPT {i+1}", {
                "Calibre": m.calibre,
                "Ampacidad": f"{m.ampacidad_ajustada_a} A",
            })

    # -----------------------------
    # AC
    # -----------------------------
    if ac:
        _tabla("⚡ AC", {
            "Calibre": ac.calibre,
            "Ampacidad": f"{ac.ampacidad_ajustada_a} A",
        })
# ==========================================================
# PROTECCIONES (🔥 CORREGIDO)
# ==========================================================
def _render_protecciones(rp):

    e = getattr(rp, "electrical", None)

    if e is None:
        st.warning("Sin protecciones")
        return

    p = getattr(e, "protecciones", None)

    if not p or not getattr(p, "ok", False):
        st.warning("Protecciones no disponibles")
        return

    _tabla("⚠ Protecciones", {
        "Fusible string": f"{getattr(p, 'fusible_string', '—')} A",
        "Breaker AC": f"{getattr(p, 'ocpd_ac', {}).tamano_a if hasattr(p, 'ocpd_ac') else '—'} A",
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
