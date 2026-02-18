# app.py
from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

# === FIX: asegurar que Python encuentre los paquetes (core, reportes) ===
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# === IMPORTS CORRECTOS (tu repo usa core/ y reportes/) ===
from core.modelo import Datosproyecto
from core.rutas import preparar_salida, money_L, num
from core.orquestador import ejecutar_evaluacion

from reportes.charts import generar_charts
from reportes.layout_paneles import generar_layout_paneles
from reportes.pdf.builder import generar_pdf_profesional


st.set_page_config(page_title="FV Engine", layout="wide")

st.title("Evaluación Fotovoltaica (FV Engine)")

with st.sidebar:
    st.header("Datos")
    cliente = st.text_input("Cliente", "Cliente ejemplo")
    ubicacion = st.text_input("Ubicación", "Honduras")
    tarifa = st.number_input("Tarifa energía (L/kWh)", value=4.998, min_value=0.0, step=0.001, format="%.3f")
    fijos = st.number_input("Cargos fijos (L/mes)", value=325.38, min_value=0.0, step=1.0)

    st.subheader("Consumo (12 meses)")
    consumo_str = st.text_area("kWh (12 valores separados por coma)", "1500,1800,2100,2200,2400,2300,900,950,1100,1200,1900,1700")
    consumo_12m = [float(x.strip()) for x in consumo_str.split(",") if x.strip()]

    st.subheader("FV")
    prod_base = st.number_input("Producción base (kWh/kWp/mes)", value=145.0, min_value=1.0, step=1.0)
    factores_str = st.text_area("Factores FV (12 valores)", "0.95,0.97,1.02,1.05,1.08,1.05,0.98,1.00,1.03,1.04,1.00,0.93")
    factores = [float(x.strip()) for x in factores_str.split(",") if x.strip()]
    cobertura = st.slider("Cobertura objetivo", 0.10, 1.00, 0.64, 0.01)

    st.subheader("Costos/Finanzas")
    costo_usd_kwp = st.number_input("Costo USD/kWp", value=1200.0, min_value=1.0, step=10.0)
    tcambio = st.number_input("Tipo cambio", value=27.0, min_value=0.1, step=0.1)
    tasa = st.number_input("Tasa anual (decimal)", value=0.08, min_value=0.0, max_value=0.99, step=0.01)
    plazo = st.number_input("Plazo (años)", value=10, min_value=1, step=1)
    pct_fin = st.slider("% financiado", 0.10, 1.00, 1.00, 0.01)
    om_pct = st.number_input("O&M anual (% CAPEX) decimal", value=0.01, min_value=0.0, max_value=0.20, step=0.005)

    run = st.button("Calcular y generar PDF")

if run:
    datos = DatosProyecto(
        cliente=cliente,
        ubicacion=ubicacion,
        consumo_12m=consumo_12m,
        tarifa_energia=tarifa,
        cargos_fijos=fijos,
        prod_base_kwh_kwp_mes=prod_base,
        factores_fv_12m=factores,
        cobertura_objetivo=cobertura,
        costo_usd_kwp=costo_usd_kwp,
        tcambio=tcambio,
        tasa_anual=tasa,
        plazo_anios=int(plazo),
        porcentaje_financiado=pct_fin,
        om_anual_pct=om_pct,
    )

    paths = preparar_salida("salidas")
    res = ejecutar_evaluacion(datos)

    generar_charts(res["tabla_12m"], paths)
    generar_layout_paneles(
        n_paneles=int(res["sizing"]["n_paneles"]),
        out_path=paths["layout_paneles"],
        max_cols=7,
        dos_aguas=True,
        gap_cumbrera_m=0.35
    )
    pdf_path = generar_pdf_profesional(res, datos, paths)

    c1, c2, c3 = st.columns(3)
    c1.metric("Sistema (kWp DC)", num(float(res["sizing"]["kwp_dc"]), 2))
    c2.metric("Cuota mensual", money_L(float(res["cuota_mensual"])))
    c3.metric("Estado", res["evaluacion"]["estado"])

    st.image(paths["chart_energia"], caption="Energía")
    st.image(paths["chart_neto"], caption="Flujo neto")
    st.image(paths["chart_generacion"], caption="Generación FV útil")
    st.image(paths["layout_paneles"], caption="Layout paneles")

    with open(pdf_path, "rb") as f:
        st.download_button("Descargar PDF", data=f, file_name="reporte_evaluacion_fv.pdf", mime="application/pdf")
