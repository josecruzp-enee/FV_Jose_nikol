from __future__ import annotations
from typing import Tuple, List, Dict
import streamlit as st
from core.servicios.analisis_cobertura import analizar_cobertura

"""
PASO 2 — CONSUMO ENERGÉTICO
FV Engine

UI Layer — captura y valida consumo mensual + tarifa
"""

# ==========================================================
# CONSTANTES
# ==========================================================
_MESES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
]

# ==========================================================
# RENDER PRINCIPAL
# ==========================================================
# ==========================================================
# RENDER PRINCIPAL (con columnas)
# ==========================================================
def render(ctx) -> None:
    """
    Renderiza inputs de consumo energético en 3 columnas,
    actualiza ctx.consumo, muestra métricas y escenarios FV.
    """
    consumo = getattr(ctx, "consumo", {})

    # Inicializar campos si no existen
    consumo.setdefault("kwh_12m", [0.0]*12)
    consumo.setdefault("cargos_fijos_L_mes", 0.0)
    consumo.setdefault("tarifa_energia_L_kwh", 0.0)
    consumo.setdefault("fuente", "manual")

    st.markdown("### Consumo energético")

    # ======================================================
    # Inputs de consumo mensual en 3 columnas
    # ======================================================
    n_cols = 3
    cols = st.columns(n_cols)

    for i, mes in enumerate(_MESES):
        col = cols[i % n_cols]
        consumo["kwh_12m"][i] = col.number_input(
            f"{mes} (kWh)",
            value=consumo["kwh_12m"][i],
            min_value=0.0,
            format="%.2f",
            key=f"kwh_{i}"
        )

    # ======================================================
    # Inputs de cargos y tarifa
    # ======================================================
    c1, c2 = st.columns(2)

    consumo["cargos_fijos_L_mes"] = c1.number_input(
        "Cargos fijos L/Mes",
        value=consumo["cargos_fijos_L_mes"],
        min_value=0.0,
        format="%.2f",
    )

    consumo["tarifa_energia_L_kwh"] = c2.number_input(
        "Tarifa energía L/kWh",
        value=consumo["tarifa_energia_L_kwh"],
        min_value=0.0,
        format="%.2f",
    )

    # Actualizar ctx
    ctx.consumo = consumo

    # Mostrar métricas
    total = sum(consumo["kwh_12m"])
    promedio = total / 12
    st.write(f"Consumo anual total: {total:.2f} kWh")
    st.write(f"Consumo promedio mensual: {promedio:.2f} kWh")

    # Llamar análisis exploratorio
    render_analisis_cobertura(ctx)

# ==========================================================
# ANÁLISIS COBERTURA FV
# ==========================================================
def render_analisis_cobertura(ctx):
    """
    Ejecuta análisis de diferentes tamaños de FV
    """
    consumo = ctx.consumo

    # Valores de ejemplo para cálculo preliminar
    potencia_panel_kw = 0.55       # 550 W por panel
    energia_1kwp_anual = 1500.0    # kWh anual por kWp instalado

    try:
        escenarios = analizar_cobertura(
            consumo_anual_kwh=sum(consumo["kwh_12m"]),
            potencia_panel_kw=potencia_panel_kw,
            energia_1kwp_anual=energia_1kwp_anual,
            tarifa_energia=consumo["tarifa_energia_L_kwh"],
        )
    except Exception as e:
        st.error(f"No se pudo calcular escenarios FV: {e}")
        return

    st.write("### Escenarios FV")
    st.dataframe([e.__dict__ for e in escenarios])

# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:
    """
    Valida que los datos de consumo sean correctos
    """
    errores: List[str] = []
    consumo = getattr(ctx, "consumo", {})

    kwh = consumo.get("kwh_12m", [])
    if len(kwh) != 12:
        errores.append("Se deben ingresar 12 meses de consumo.")
    if any(x < 0 for x in kwh):
        errores.append("No se permiten consumos negativos.")
    if sum(kwh) <= 0:
        errores.append("Al menos un mes debe tener consumo > 0.")

    return len(errores) == 0, errores

# ==========================================================
# RENDER DEMANDA vs FV (opcional)
# ==========================================================
def render_demanda_vs_fv(ctx, energia_mensual_kwh):
    """
    Grafica demanda mensual vs generación FV estimada
    """
    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.DataFrame({
        "Demanda": ctx.consumo["kwh_12m"],
        "Generación FV": energia_mensual_kwh
    }, index=_MESES)

    st.line_chart(df)
