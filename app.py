# app.py
from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st

# === asegurar imports del repo ===
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.modelo import Datosproyecto
from core.orquestador import ejecutar_evaluacion
from core.rutas import preparar_salida, money_L, num

from electrical.estimador import calcular_paquete_electrico

# (opcionales si ya los usas)
from reportes.generar_charts import generar_charts
from reportes.generar_layout_paneles import generar_layout_paneles
from reportes.generar_pdf_profesional import generar_pdf_profesional
from ui.router import PasoWizard, render_wizard
from ui import datos_cliente, consumo_energetico, sistema_fv, seleccion_equipos


pasos = [
        PasoWizard(1, "Datos cliente", datos_cliente.render, datos_cliente.validar, requiere=[]),
        PasoWizard(2, "Consumo energético", consumo_energetico.render, consumo_energetico.validar, requiere=[1]),
        PasoWizard(3, "Sistema FV", sistema_fv.render, sistema_fv.validar, requiere=[1, 2]),
        PasoWizard(4, "Selección de equipos", seleccion_equipos.render, seleccion_equipos.validar, requiere=[1, 2, 3]),
    ]

render_wizard(pasos)

# UI helpers (si ya los creaste)
try:
    from ui.secciones import ui_equipos, ui_cableado
except Exception:
    ui_equipos = None
    ui_cableado = None


def _leer_lista_floats(texto: str) -> list[float]:
    vals = [x.strip() for x in (texto or "").split(",") if x.strip()]
    return [float(x) for x in vals]


def _armar_datos_desde_ui() -> Datosproyecto:
    with st.sidebar:
        st.header("Datos del proyecto")

        cliente = st.text_input("Cliente", "Cliente ejemplo")
        ubicacion = st.text_input("Ubicación", "Honduras")

        tarifa = st.number_input("Tarifa energía (L/kWh)", value=4.998, min_value=0.0, step=0.001, format="%.3f")
        fijos = st.number_input("Cargos fijos (L/mes)", value=325.38, min_value=0.0, step=1.0)

        st.subheader("Consumo (12 meses)")
        consumo_str = st.text_area(
            "kWh (12 valores separados por coma)",
            "1500,1800,2100,2200,2400,2300,900,950,1100,1200,1900,1700"
        )
        consumo_12m = _leer_lista_floats(consumo_str)

        st.subheader("FV")
        prod_base = st.number_input("Producción base (kWh/kWp/mes)", value=145.0, min_value=1.0, step=1.0)
        factores_str = st.text_area(
            "Factores FV (12 valores)",
            "0.95,0.97,1.02,1.05,1.08,1.05,0.98,1.00,1.03,1.04,1.00,0.93"
        )
        factores = _leer_lista_floats(factores_str)
        cobertura = st.slider("Cobertura objetivo", 0.10, 1.00, 0.64, 0.01)

        st.subheader("Costos/Finanzas")
        costo_usd_kwp = st.number_input("Costo USD/kWp", value=1200.0, min_value=1.0, step=10.0)
        tcambio = st.number_input("Tipo cambio", value=27.0, min_value=0.1, step=0.1)
        tasa = st.number_input("Tasa anual (decimal)", value=0.08, min_value=0.0, max_value=0.99, step=0.01)
        plazo = st.number_input("Plazo (años)", value=10, min_value=1, step=1)
        pct_fin = st.slider("% financiado", 0.10, 1.00, 1.00, 0.01)
        om_pct = st.number_input("O&M anual (% CAPEX) decimal", value=0.01, min_value=0.0, max_value=0.20, step=0.005)

        # Secciones eléctricas (si existen)
        if ui_equipos:
            ui_equipos(st.session_state)
        if ui_cableado:
            ui_cableado(st.session_state)

    # Validaciones mínimas
    if len(consumo_12m) != 12:
        raise ValueError("Consumo: debes ingresar exactamente 12 valores.")
    if len(factores) != 12:
        raise ValueError("Factores FV: debes ingresar exactamente 12 valores.")

    return Datosproyecto(
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


def main() -> None:
    st.set_page_config(page_title="FV Engine", layout="wide")
    st.title("Evaluación Fotovoltaica (FV Engine)")

    try:
        datos = _armar_datos_desde_ui()
    except Exception as e:
        st.error(str(e))
        st.stop()

    run = st.sidebar.button("Calcular y generar", type="primary")

    if not run:
        st.info("Configura los datos en la barra lateral y presiona **Calcular y generar**.")
        return

    # 1) Motor FV
    res = ejecutar_evaluacion(datos)

    # 2) Eléctrico (orquestado)
    pkg = calcular_paquete_electrico(res=res, state=st.session_state)

    # 3) KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Sistema (kWp DC)", num(float(res["sizing"]["kwp_dc"]), 2))
    c2.metric("Cuota mensual", money_L(float(res["cuota_mensual"])))
    c3.metric("Estado", res["evaluacion"]["estado"])

    # 4) Mostrar eléctrico
    st.subheader("Configuración eléctrica DC (strings) — referencial")
    for line in pkg["texto_ui"]["strings"]:
        st.write("• " + line)
    if pkg["texto_ui"]["checks"]:
        st.warning("\n".join(pkg["texto_ui"]["checks"]))

    st.subheader("Cableado (AC/DC) — referencial")
    for line in pkg["texto_ui"]["cableado"]:
        st.write("• " + line)
    st.caption(pkg["texto_ui"]["disclaimer"])

    # 5) Salidas (charts/layout/pdf)
    paths = preparar_salida("salidas")

    # generar charts (CORRECTO)
    try:
        charts = generar_charts(res["tabla_12m"], paths["charts_dir"])
        res["charts"] = charts
        paths.update(charts)  # opcional: paths["chart_energia"] etc.
    except Exception as e:
        st.warning(f"No se pudieron generar charts: {e}")

    try:
        generar_layout_paneles(
            n_paneles=int(res["sizing"]["n_paneles"]),
            out_path=paths["layout_paneles"],
            max_cols=7,
            dos_aguas=bool(st.session_state.get("dos_aguas", True)),
            gap_cumbrera_m=0.35,
        )
    except Exception:
        pass

    try:
        pdf_path = generar_pdf_profesional(res, datos, paths)
        with open(pdf_path, "rb") as f:
            st.download_button("Descargar PDF", data=f, file_name="reporte_evaluacion_fv.pdf", mime="application/pdf")
    except Exception as e:
        st.warning(f"No se pudo generar PDF aún: {e}")


main()

