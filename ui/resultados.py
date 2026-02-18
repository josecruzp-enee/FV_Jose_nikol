# ui/resultados.py
from __future__ import annotations
from typing import List, Tuple

import streamlit as st

from core.rutas import preparar_salida, money_L, num
from reportes.generar_charts import generar_charts
from reportes.generar_layout_paneles import generar_layout_paneles
from reportes.generar_pdf_profesional import generar_pdf_profesional


def render(ctx) -> None:
    st.markdown("### Resultados y propuesta")

    if ctx.resultado_core is None:
        st.error("No hay resultados del motor FV. Genere primero la ingeniería eléctrica (Paso 5).")
        return
    if ctx.resultado_electrico is None:
        st.error("No hay resultados eléctricos. Genere primero la ingeniería eléctrica (Paso 5).")
        return

    res = ctx.resultado_core
    pkg = ctx.resultado_electrico

    # ===== KPIs =====
    c1, c2, c3 = st.columns(3)
    c1.metric("Sistema (kWp DC)", num(float(res["sizing"]["kwp_dc"]), 2))
    c2.metric("Cuota mensual", money_L(float(res["cuota_mensual"])))
    c3.metric("Estado", res["evaluacion"]["estado"])

    st.divider()

    # ===== Mostrar resumen eléctrico =====
    st.subheader("Strings DC (referencial)")
    for line in pkg["texto_ui"]["strings"]:
        st.write("• " + line)
    if pkg["texto_ui"]["checks"]:
        st.warning("\n".join(pkg["texto_ui"]["checks"]))

    st.subheader("Cableado AC/DC (referencial)")
    for line in pkg["texto_ui"]["cableado"]:
        st.write("• " + line)
    st.caption(pkg["texto_ui"]["disclaimer"])

    st.divider()

    # ===== Generación de artefactos =====
    st.markdown("#### Generar propuesta (PDF)")

    col_a, col_b = st.columns([1, 2])
    with col_a:
        run = st.button("Generar PDF", type="primary")
    with col_b:
        st.caption("Genera charts, layout y PDF profesional usando los datos ya calculados.")

    if not run:
        return

    # 1) Salidas
    paths = preparar_salida("salidas")

    # 2) Charts
    try:
        charts = generar_charts(res["tabla_12m"], paths["charts_dir"])
        res["charts"] = charts
        paths.update(charts)
    except Exception as e:
        st.warning(f"No se pudieron generar charts: {e}")

    # 3) Layout paneles
    try:
        generar_layout_paneles(
            n_paneles=int(res["sizing"]["n_paneles"]),
            out_path=paths["layout_paneles"],
            max_cols=7,
            dos_aguas=bool(ctx.electrico.get("dos_aguas", True)) if hasattr(ctx, "electrico") else True,
            gap_cumbrera_m=0.35,
        )
    except Exception as e:
        st.warning(f"No se pudo generar layout de paneles: {e}")

    # 4) PDF
    try:
        # OJO: generar_pdf_profesional espera (res, datos, paths)
        # En este wizard aún no estamos guardando "datos" como objeto Datosproyecto.
        # Solución correcta: guardar datos en ctx en Paso 5 cuando ejecutas core.
        if not hasattr(ctx, "datos_proyecto") or ctx.datos_proyecto is None:
            st.error("Falta ctx.datos_proyecto. En Paso 5 guarda datos (Datosproyecto) en ctx.datos_proyecto.")
            return

        pdf_path = generar_pdf_profesional(res, ctx.datos_proyecto, paths)
        ctx.artefactos["pdf"] = pdf_path

        with open(pdf_path, "rb") as f:
            st.download_button(
                "Descargar PDF",
                data=f,
                file_name="reporte_evaluacion_fv.pdf",
                mime="application/pdf",
            )

        st.success("PDF generado.")
    except Exception as e:
        st.warning(f"No se pudo generar PDF aún: {e}")


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []
    if ctx.resultado_core is None:
        errores.append("No hay resultados del motor FV (genere en Paso 5).")
    if ctx.resultado_electrico is None:
        errores.append("No hay resultados eléctricos (genere en Paso 5).")
    return (len(errores) == 0), errores
