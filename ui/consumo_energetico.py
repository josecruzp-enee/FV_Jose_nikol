from __future__ import annotations
from typing import List, Tuple
import streamlit as st
from core.servicios.analisis_cobertura import analizar_cobertura

_MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

def render(ctx) -> None:
    """
    Paso 2: Consumo energético
    Captura consumo mensual, tarifa y cargos fijos,
    calcula total, promedio y potencia FV estimada.
    """

    # Inicializar ctx.consumo si no existe
    consumo = getattr(ctx, "consumo", {})
    consumo.setdefault("kwh_12m", [0.0]*12)
    consumo.setdefault("cargos_fijos_L_mes", 0.0)
    consumo.setdefault("tarifa_energia_L_kwh", 0.0)
    consumo.setdefault("fuente", "manual")

    st.markdown("### Consumo energético")

    # --- 3-4 columnas para meses ---
    n_cols = 4
    cols = st.columns(n_cols)
    for i, mes in enumerate(_MESES):
        c = cols[i % n_cols]
        with c:
            consumo["kwh_12m"][i] = st.number_input(
                f"{mes} (kWh)",
                value=consumo["kwh_12m"][i],
                min_value=0.0,
                step=0.1,
                format="%.2f"
            )

    # Tarifas y cargos fijos en fila aparte
    c1, c2 = st.columns(2)
    with c1:
        consumo["cargos_fijos_L_mes"] = st.number_input(
            "Cargos fijos L/Mes",
            value=consumo["cargos_fijos_L_mes"],
            min_value=0.0,
            step=1.0
        )
    with c2:
        consumo["tarifa_energia_L_kwh"] = st.number_input(
            "Tarifa energía L/kWh",
            value=consumo["tarifa_energia_L_kwh"],
            min_value=0.0,
            step=0.01
        )

    # --- Totales y métricas ---
    total_anual = sum(consumo["kwh_12m"])
    promedio_mensual = total_anual / 12
    st.write(f"**Consumo anual total:** {total_anual:.2f} kWh")
    st.write(f"**Consumo promedio mensual:** {promedio_mensual:.2f} kWh")

    # --- Cálculo preliminar para dimensionamiento ---
    # Nota: potencia_panel_kw y energia_1kwp_anual deberían venir de catálogo o defaults
    potencia_panel_kw = 0.55  # ejemplo: panel de 550 W
    energia_1kwp_anual = 1500  # ejemplo: producción anual por kWp

    potencia_fv_kw = total_anual / energia_1kwp_anual
    n_paneles_total = int(round(potencia_fv_kw / potencia_panel_kw))

    consumo["potencia_fv_kw"] = potencia_fv_kw
    consumo["n_paneles_total"] = n_paneles_total

    ctx.consumo = consumo

    # --- Análisis de cobertura (opcional visualización) ---
    if total_anual > 0:
        escenarios = analizar_cobertura(
            consumo_anual_kwh=total_anual,
            potencia_panel_kw=potencia_panel_kw,
            energia_1kwp_anual=energia_1kwp_anual,
            tarifa_energia=consumo["tarifa_energia_L_kwh"]
        )
        st.markdown("### Escenarios de cobertura FV")
        import pandas as pd
        st.dataframe(pd.DataFrame([vars(e) for e in escenarios]))


def validar(ctx) -> Tuple[bool, List[str]]:
    """
    Valida que se hayan ingresado los 12 meses y al menos un consumo positivo.
    """
    errores: List[str] = []
    consumo = getattr(ctx, "consumo", {})
    kwh = consumo.get("kwh_12m", [])
    if len(kwh) != 12:
        errores.append("Debe ingresar consumo para los 12 meses.")
    if any(x < 0 for x in kwh):
        errores.append("No se permiten valores negativos.")
    if sum(kwh) <= 0:
        errores.append("Al menos un mes debe tener consumo > 0.")
    return len(errores) == 0, errores
