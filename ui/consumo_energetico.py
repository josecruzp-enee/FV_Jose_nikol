# ui/consumo_energetico.py
from __future__ import annotations
from typing import List, Tuple

import streamlit as st
import pandas as pd

from core.servicios.analisis_cobertura import analizar_cobertura
from core.aplicacion.orquestador import ejecutar_estudio


_MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]


# ---------------------------------------------------------
# Análisis de cobertura FV
# ---------------------------------------------------------

def render_analisis_cobertura(ctx):
    """
    Ejecuta el análisis de cobertura usando el servicio del core
    y muestra los escenarios de sistema FV.
    """

    st.markdown("### Análisis de tamaño del sistema FV")

    if st.button("Analizar escenarios de cobertura"):

        try:

            escenarios = analizar_cobertura(
                datos=ctx,
                deps=ctx.deps,
                ejecutar_estudio=ejecutar_estudio,
            )

            if not escenarios:
                st.warning("No se generaron escenarios.")
                return

            df = pd.DataFrame(escenarios)

            df = df.rename(columns={
                "cobertura": "Cobertura %",
                "kw_fv": "Sistema FV (kW)",
                "paneles": "Paneles",
                "roi": "ROI %",
                "payback": "Payback (años)",
            })

            st.dataframe(df, use_container_width=True)

            if "ROI %" in df.columns:

                st.markdown("#### ROI vs Cobertura")

                chart = df.set_index("Cobertura %")["ROI %"]

                st.line_chart(chart)

        except Exception as e:

            st.error(f"Error ejecutando análisis de cobertura: {e}")


# ---------------------------------------------------------
# UI Consumo energético
# ---------------------------------------------------------

def render(ctx) -> None:

    st.markdown("### Consumo energético (últimos 12 meses)")

    c = ctx.consumo

    col1, col2, col3 = st.columns(3)

    with col1:
        c["tarifa_energia_L_kwh"] = st.number_input(
            "Tarifa energía (L/kWh)",
            min_value=0.0,
            step=0.1,
            value=float(c.get("tarifa_energia_L_kwh", 0.0)),
        )

    with col2:
        c["cargos_fijos_L_mes"] = st.number_input(
            "Cargos fijos (L/mes)",
            min_value=0.0,
            step=10.0,
            value=float(c.get("cargos_fijos_L_mes", 0.0)),
        )

    with col3:
        c["fuente"] = st.selectbox(
            "Fuente de datos",
            options=["manual"],
            index=0,
            help="Por ahora manual. Luego: recibo/CSV.",
        )

    st.markdown("#### kWh por mes")

    kwh = list(c.get("kwh_12m", [0.0] * 12))

    if len(kwh) != 12:
        kwh = [0.0] * 12

    # grid 4x3 para inputs
    for fila in range(3):

        cols = st.columns(4)

        for j in range(4):

            i = fila * 4 + j

            with cols[j]:

                kwh[i] = st.number_input(
                    f"{_MESES[i]} (kWh)",
                    min_value=0.0,
                    step=10.0,
                    value=float(kwh[i] or 0.0),
                    key=f"kwh_{i}",
                )

    c["kwh_12m"] = kwh

    total = float(sum(kwh))
    prom = total / 12.0

    a, b = st.columns(2)

    with a:
        st.metric("Consumo anual (kWh)", f"{total:,.0f}")

    with b:
        st.metric("Promedio mensual (kWh)", f"{prom:,.0f}")

    # guardar datos
    ctx.consumo = c

    # ejecutar análisis de cobertura
    render_analisis_cobertura(ctx)


# ---------------------------------------------------------
# Validación
# ---------------------------------------------------------

def validar(ctx) -> Tuple[bool, List[str]]:

    errores: List[str] = []

    c = ctx.consumo

    kwh = c.get("kwh_12m", [])

    if not isinstance(kwh, list) or len(kwh) != 12:

        errores.append("Debe ingresar 12 valores de consumo (kWh).")

        return False, errores

    try:

        kwh_vals = [float(x) for x in kwh]

    except Exception:

        errores.append("Consumo inválido: revise que todos los meses sean numéricos.")

        return False, errores

    if any(v < 0 for v in kwh_vals):

        errores.append("Consumo inválido: no se permiten valores negativos.")

    if max(kwh_vals) <= 0:

        errores.append("Consumo inválido: al menos un mes debe ser mayor que 0 kWh.")

    tarifa = float(c.get("tarifa_energia_L_kwh", 0.0))
    cargos = float(c.get("cargos_fijos_L_mes", 0.0))

    if tarifa <= 0:
        errores.append("Ingrese una tarifa de energía (L/kWh) mayor que 0.")

    if cargos < 0:
        errores.append("Cargos fijos inválidos (no negativos).")

    return (len(errores) == 0), errores
