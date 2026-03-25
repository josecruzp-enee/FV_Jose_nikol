from __future__ import annotations
from typing import List, Tuple
import streamlit as st

_MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

def render(ctx) -> None:
    """
    Paso 2: Captura consumo mensual, tarifa y cargos fijos.
    Solo UI.
    """

    st.markdown("### Consumo energético")

    sf = st.session_state

    # ------------------------------------------------------
    # VALORES POR DEFECTO (SOLO PRIMERA VEZ)
    # ------------------------------------------------------
    sf.setdefault("kwh_12m", [10000.0]*12)
    sf.setdefault("cargos_fijos_L_mes", 200.0)
    sf.setdefault("tarifa_energia_L_kwh", 5.0)

    consumo = {
        "kwh_12m": sf["kwh_12m"],
        "cargos_fijos_L_mes": sf["cargos_fijos_L_mes"],
        "tarifa_energia_L_kwh": sf["tarifa_energia_L_kwh"],
        "fuente": "manual"
    }

    # ------------------------------------------------------
    # INPUTS MESES (3 COLUMNAS)
    # ------------------------------------------------------
    n_cols = 3
    cols = st.columns(n_cols)

    for i, mes in enumerate(_MESES):
        with cols[i % n_cols]:
            key = f"kwh_{i}"

            # inicializar cada mes
            if key not in sf:
                sf[key] = consumo["kwh_12m"][i]

            consumo["kwh_12m"][i] = st.number_input(
                f"{mes} (kWh)",
                key=key,
                min_value=0.0,
                step=0.1,
                format="%.2f"
            )

    # ------------------------------------------------------
    # TARIFAS Y CARGOS
    # ------------------------------------------------------
    c1, c2 = st.columns(2)

    with c1:
        consumo["cargos_fijos_L_mes"] = st.number_input(
            "Cargos fijos L/Mes",
            key="cargos_fijos_L_mes",
            min_value=0.0,
            step=1.0
        )

    with c2:
        consumo["tarifa_energia_L_kwh"] = st.number_input(
            "Tarifa energía L/kWh",
            key="tarifa_energia_L_kwh",
            min_value=0.0,
            step=0.01
        )

    # ------------------------------------------------------
    # TOTALES
    # ------------------------------------------------------
    total_anual = sum(consumo["kwh_12m"])
    promedio_mensual = total_anual / 12

    st.write(f"**Consumo anual total:** {total_anual:.2f} kWh")
    st.write(f"**Consumo promedio mensual:** {promedio_mensual:.2f} kWh")

    # ------------------------------------------------------
    # GUARDAR EN CONTEXTO
    # ------------------------------------------------------
    ctx.consumo = consumo


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
