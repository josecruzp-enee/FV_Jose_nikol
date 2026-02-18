# app.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

import streamlit as st

# =========================
# FIX: path del proyecto
# =========================
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# =========================
# Imports del proyecto
# =========================
from core.modelo import Datosproyecto
from core.rutas import preparar_salida, money_L, num
from core.orquestador import ejecutar_evaluacion

from reportes.generar_charts import generar_charts
from reportes.generar_layout_paneles import generar_layout_paneles
from reportes.generar_pdf_profesional import generar_pdf_profesional


# =========================
# Helpers UI / Validación
# =========================
def _parsear_lista_float(texto: str) -> List[float]:
    return [float(x.strip()) for x in (texto or "").split(",") if x.strip()]


def _validar_12(valores: List[float], nombre: str) -> Tuple[bool, str]:
    if len(valores) != 12:
        return False, f"{nombre} debe tener 12 valores. Recibidos: {len(valores)}."
    return True, ""


def _armar_datos_proyecto(
    *,
    cliente: str,
    ubicacion: str,
    tarifa: float,
    fijos: float,
    consumo_12m: List[float],
    prod_base: float,
    factores: List[float],
    cobertura: float,
    costo_usd_kwp: float,
    tcambio: float,
    tasa: float,
    plazo: int,
    pct_fin: float,
    om_pct: float,
) -> Datosproyecto:
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


def _calcular_evaluacion(datos: Datosproyecto) -> Dict[str, Any]:
    return ejecutar_evaluacion(datos)


def _calcular_strings_y_reflejar_ui(res: Dict[str, Any], datos: Datosproyecto) -> None:
    """
    Calcula strings DC (si existe el módulo electrical/strings.py),
    guarda en res y muestra en Streamlit.
    """
    try:
        from electrical.strings import plan_strings, strings_to_lines, strings_to_html

        n_paneles = int(res["sizing"]["n_paneles"])

        cfg = plan_strings(
            n_paneles=n_paneles,
            dos_aguas=True,
            vmppt_min=getattr(datos, "vmppt_min", None),
            vmppt_max=getattr(datos, "vmppt_max", None),
            vdc_max=getattr(datos, "vdc_max", None),
            t_min_c=float(getattr(datos, "t_min_c", 10.0)),
        )

        res["cfg_strings"] = cfg
        res["cfg_strings_html"] = strings_to_html(cfg)

        st.subheader("Configuración eléctrica DC (strings) — referencial")
        for line in strings_to_lines(cfg):
            st.write("• " + line)

        checks = cfg.get("checks") or []
        if checks:
            st.warning("\n".join(checks))

    except Exception as e:
        st.info(f"Bloque eléctrico (strings) aún no disponible: {e}")


def _generar_salidas(res: Dict[str, Any], datos: Datosproyecto) -> Dict[str, Any]:
    """
    Genera charts, layout y PDF. Devuelve paths.
    Contrato: generar_charts(tabla_12m, out_dir)
    """
    paths = preparar_salida("salidas")

    tabla_12m = res.get("tabla_12m") or []
    generar_charts(tabla_12m, paths["charts_dir"])

    generar_layout_paneles(
        n_paneles=int(res["sizing"]["n_paneles"]),
        out_path=paths["layout_paneles"],
        max_cols=7,
        dos_aguas=True,
        gap_cumbrera_m=0.35,
    )

    pdf_path = generar_pdf_profesional(res, datos, paths)
    paths["pdf_path"] = pdf_path
    return paths



def _mostrar_resultados(res: Dict[str, Any], paths: Dict[str, Any]) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Sistema (kWp DC)", num(float(res["sizing"]["kwp_dc"]), 2))
    c2.metric("Cuota mensual", money_L(float(res["cuota_mensual"])))
    c3.metric("Estado", res["evaluacion"]["estado"])

    if paths.get("chart_energia"):
        st.image(paths["chart_energia"], caption="Energía")
    if paths.get("chart_neto"):
        st.image(paths["chart_neto"], caption="Flujo neto")
    if paths.get("chart_generacion"):
        st.image(paths["chart_generacion"], caption="Generación FV útil")
    if paths.get("layout_paneles"):
        st.image(paths["layout_paneles"], caption="Layout paneles")

    pdf_path = paths.get("pdf_path")
    if pdf_path:
        with open(pdf_path, "rb") as f:
            st.download_button(
                "Descargar PDF",
                data=f,
                file_name="reporte_evaluacion_fv.pdf",
                mime="application/pdf",
            )


# =========================
# UI principal
# =========================
def main() -> None:
    st.set_page_config(page_title="FV Engine", layout="wide")
    st.title("Evaluación Fotovoltaica (FV Engine)")

    with st.sidebar:
        st.header("Datos")
        cliente = st.text_input("Cliente", "Cliente ejemplo")
        ubicacion = st.text_input("Ubicación", "Honduras")
        tarifa = st.number_input("Tarifa energía (L/kWh)", value=4.998, min_value=0.0, step=0.001, format="%.3f")
        fijos = st.number_input("Cargos fijos (L/mes)", value=325.38, min_value=0.0, step=1.0)

        st.subheader("Consumo (12 meses)")
        consumo_str = st.text_area(
            "kWh (12 valores separados por coma)",
            "1500,1800,2100,2200,2400,2300,900,950,1100,1200,1900,1700",
        )
        consumo_12m = _parsear_lista_float(consumo_str)

        st.subheader("FV")
        prod_base = st.number_input("Producción base (kWh/kWp/mes)", value=145.0, min_value=1.0, step=1.0)
        factores_str = st.text_area(
            "Factores FV (12 valores)",
            "0.95,0.97,1.02,1.05,1.08,1.05,0.98,1.00,1.03,1.04,1.00,0.93",
        )
        factores = _parsear_lista_float(factores_str)
        cobertura = st.slider("Cobertura objetivo", 0.10, 1.00, 0.64, 0.01)

        st.subheader("Costos/Finanzas")
        costo_usd_kwp = st.number_input("Costo USD/kWp", value=1200.0, min_value=1.0, step=10.0)
        tcambio = st.number_input("Tipo cambio", value=27.0, min_value=0.1, step=0.1)
        tasa = st.number_input("Tasa anual (decimal)", value=0.08, min_value=0.0, max_value=0.99, step=0.01)
        plazo = st.number_input("Plazo (años)", value=10, min_value=1, step=1)
        pct_fin = st.slider("% financiado", 0.10, 1.00, 1.00, 0.01)
        om_pct = st.number_input("O&M anual (% CAPEX) decimal", value=0.01, min_value=0.0, max_value=0.20, step=0.005)

        run = st.button("Calcular y generar PDF")

    if not run:
        return

    ok, msg = _validar_12(consumo_12m, "Consumo (12 meses)")
    if not ok:
        st.error(msg)
        return

    ok, msg = _validar_12(factores, "Factores FV (12 meses)")
    if not ok:
        st.error(msg)
        return

    datos = _armar_datos_proyecto(
        cliente=cliente,
        ubicacion=ubicacion,
        tarifa=tarifa,
        fijos=fijos,
        consumo_12m=consumo_12m,
        prod_base=prod_base,
        factores=factores,
        cobertura=cobertura,
        costo_usd_kwp=costo_usd_kwp,
        tcambio=tcambio,
        tasa=tasa,
        plazo=int(plazo),
        pct_fin=pct_fin,
        om_pct=om_pct,
    )

    with st.spinner("Calculando evaluación..."):
        res = _calcular_evaluacion(datos)

    _calcular_strings_y_reflejar_ui(res, datos)

    with st.spinner("Generando reportes (charts/layout/PDF)..."):
        paths = _generar_salidas(res, datos)

    _mostrar_resultados(res, paths)


if __name__ == "__main__":
    main()
