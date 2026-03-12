from __future__ import annotations
from typing import Tuple, List
import streamlit as st
from core.servicios.analisis_cobertura import analizar_escenarios_fv


"""
PASO 2 — CONSUMO ENERGÉTICO
FV Engine

Este módulo implementa el segundo paso del wizard de la interfaz de usuario.

OBJETIVO
--------
Capturar y validar el consumo energético del usuario durante los últimos
12 meses junto con los parámetros de facturación eléctrica.

Este módulo pertenece a la capa:

    UI / Presentation Layer


FRONTERA DEL MÓDULO
-------------------

Entrada:
    WizardCtx (estado global del wizard)

Salida:
    ctx.consumo actualizado


DEPENDENCIAS PERMITIDAS
-----------------------

streamlit
pandas
core.servicios.analisis_cobertura


DEPENDENCIAS PROHIBIDAS
-----------------------

Este módulo NO puede importar:

    electrical.*
    paneles.*
    nec.*
    finanzas.*

La UI no realiza cálculos eléctricos ni dimensionamiento.


RESPONSABILIDADES
-----------------

Este módulo se encarga de:

    1. Capturar consumo mensual (12 meses)
    2. Capturar tarifa eléctrica
    3. Capturar cargos fijos
    4. Validar datos ingresados
    5. Mostrar métricas de consumo
    6. Ejecutar análisis exploratorio de cobertura FV
    7. Mostrar gráfica Demanda vs Generación FV


NO ES RESPONSABLE DE

    dimensionamiento FV
    cálculo de strings
    cálculo energético real
    cálculo NEC
    cálculos financieros

Estos cálculos pertenecen al motor FV.
"""

ENTRADA DEL MÓDULO
------------------

ctx : WizardCtx

El módulo utiliza principalmente:

ctx.consumo


ESTRUCTURA DE ctx.consumo
-------------------------

ctx.consumo = {

    "kwh_12m": list[float],      # consumo mensual (12 valores)

    "cargos_fijos_L_mes": float, # cargo fijo factura

    "tarifa_energia_L_kwh": float, # tarifa variable energía

    "fuente": str                # manual | recibo | csv
}


VARIABLES INTERNAS IMPORTANTES
------------------------------

_MESES : list[str]

Lista de meses usada para:

    UI
    tablas
    gráficos


kwh : list[float]

Vector temporal usado para capturar el consumo mensual.


total : float

Consumo total anual.


prom : float

Consumo promedio mensual.


energia_mensual_fv : list[float]

Vector temporal usado únicamente para visualización
de la gráfica Demanda vs FV.


FUNCIONES DEL MÓDULO
--------------------


render(ctx)

    Función principal del paso del wizard.

    Responsabilidades:

        - renderizar inputs de consumo
        - capturar valores
        - actualizar ctx.consumo
        - mostrar métricas
        - ejecutar análisis de cobertura
        - mostrar gráfica comparativa

    Entrada:

        ctx : WizardCtx

    Salida:

        ctx.consumo actualizado



render_analisis_cobertura(ctx)

    Ejecuta un análisis exploratorio de diferentes
    tamaños de sistema FV.

    Utiliza:

        core.servicios.analisis_cobertura


    Entrada:

        consumo_anual
        tarifa_energia

    Salida:

        tabla de escenarios FV




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
    
    if "kwh_12m" not in consumo:
        consumo["kwh_12m"] = [0.0]*12
    if "cargos_fijos_L_mes" not in consumo:
        consumo["cargos_fijos_L_mes"] = 0.0
    if "tarifa_energia_L_kwh" not in consumo:
        consumo["tarifa_energia_L_kwh"] = 0.0
    if "fuente" not in consumo:
        consumo["fuente"] = "manual"
    
    st.markdown("### Consumo energético")
    
    # Captura consumo mensual
    for i, mes in enumerate(_MESES):
        consumo["kwh_12m"][i] = st.number_input(
            f"Consumo {mes}", value=consumo["kwh_12m"][i], min_value=0.0
        )
    
    consumo["cargos_fijos_L_mes"] = st.number_input(
        "Cargos fijos L/Mes", value=consumo["cargos_fijos_L_mes"], min_value=0.0
    )
    
    consumo["tarifa_energia_L_kwh"] = st.number_input(
        "Tarifa energía L/kWh", value=consumo["tarifa_energia_L_kwh"], min_value=0.0
    )
    
    # Actualizar ctx
    ctx.consumo = consumo
    
    # Mostrar métricas simples
    total = sum(consumo["kwh_12m"])
    promedio = total / 12
    st.write(f"Consumo anual total: {total:.2f} kWh")
    st.write(f"Consumo promedio mensual: {promedio:.2f} kWh")
    
    # Llamar análisis exploratorio (mock)
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
