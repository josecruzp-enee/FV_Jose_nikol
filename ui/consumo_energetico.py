from __future__ import annotations
from typing import Tuple, List
import streamlit as st
from core.servicios.analisis_cobertura import analizar_escenarios_fv
import pandas as pd

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
def render(ctx) -> None:
    """
    Renderiza inputs de consumo energético, actualiza ctx.consumo,
    muestra métricas y gráficas comparativas.
    """
    consumo = getattr(ctx, "consumo", {})
    
    # Inicializar si no existen
    consumo.setdefault("kwh_12m", [0.0]*12)
    consumo.setdefault("cargos_fijos_L_mes", 0.0)
    consumo.setdefault("tarifa_energia_L_kwh", 0.0)
    consumo.setdefault("fuente", "manual")
    
    st.markdown("### Consumo energético")
    
    # Captura consumo mensual
    for i, mes in enumerate(_MESES):
        consumo["kwh_12m"][i] = st.number_input(
            f"Consumo {mes} (kWh)", value=consumo["kwh_12m"][i], min_value=0.0
        )
    
    consumo["cargos_fijos_L_mes"] = st.number_input(
        "Cargos fijos L/Mes", value=consumo["cargos_fijos_L_mes"], min_value=0.0
    )
    
    consumo["tarifa_energia_L_kwh"] = st.number_input(
        "Tarifa energía L/kWh", value=consumo["tarifa_energia_L_kwh"], min_value=0.0
    )
    
    ctx.consumo = consumo
    
    # Mostrar métricas simples
    total = sum(consumo["kwh_12m"])
    promedio = total / 12
    st.write(f"Consumo anual total: {total:.2f} kWh")
    st.write(f"Consumo promedio mensual: {promedio:.2f} kWh")
    
    # Análisis de cobertura
    render_analisis_cobertura(ctx)

# ==========================================================
# ANÁLISIS COBERTURA FV
# ==========================================================
def render_analisis_cobertura(ctx):
    """
    Ejecuta análisis exploratorio de diferentes tamaños de FV
    """
    consumo = ctx.consumo
    escenarios = analizar_escenarios_fv(
        consumo_anual=sum(consumo["kwh_12m"]),
        tarifa_energia=consumo["tarifa_energia_L_kwh"]
    )
    st.write("### Escenarios FV")
    st.dataframe(escenarios)

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
# RENDER DEMANDA vs FV
# ==========================================================
def render_demanda_vs_fv(ctx, energia_mensual_kwh: list[float]):
    """
    Grafica demanda mensual vs generación FV estimada
    """
    df = pd.DataFrame({
        "Demanda": ctx.consumo["kwh_12m"],
        "Generación FV": energia_mensual_kwh
    }, index=_MESES)

    st.line_chart(df)
