from __future__ import annotations

from typing import List, Tuple, Dict
import streamlit as st


_MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


# ======================================================
# PERFIL HORARIO BASE EN kW
# ======================================================

from typing import Dict

from typing import Dict


def obtener_perfil_kw_24h() -> Dict[int, float]:
    """
    Perfil residencial con poca presencia durante el día
    y tres aires acondicionados de 12,000 BTU funcionando
    principalmente durante la noche.

    El nombre se conserva por compatibilidad.

    Consumo aproximado:
    - Consumo total: 1,756 kWh/mes
    - Consumo diario promedio: 58.54 kWh/día
    """

    return {
        0: 4.10,
        1: 3.72,
        2: 3.30,
        3: 3.00,
        4: 2.80,
        5: 2.40,
        6: 1.29,
        7: 1.64,
        8: 1.06,
        9: 0.76,
        10: 0.65,
        11: 0.65,
        12: 0.82,
        13: 0.76,
        14: 0.70,
        15: 0.76,
        16: 0.94,
        17: 1.41,
        18: 2.58,
        19: 4.50,
        20: 5.60,
        21: 5.50,
        22: 5.00,
        23: 4.60,
    }
# ======================================================
# VALIDACIONES PERFIL HORARIO
# ======================================================

def validar_perfil_kw_24h(perfil_kw_24h: Dict[int, float]) -> None:
    """
    Valida perfil horario técnico en kW.
    """

    if not isinstance(perfil_kw_24h, dict):
        raise TypeError("El perfil horario debe ser un diccionario {hora: kW}.")

    if set(perfil_kw_24h.keys()) != set(range(24)):
        raise ValueError("El perfil horario debe contener exactamente las horas 0 a 23.")

    if any(valor < 0 for valor in perfil_kw_24h.values()):
        raise ValueError("El perfil horario en kW no puede contener valores negativos.")


# ======================================================
# CÁLCULOS PERFIL HORARIO
# ======================================================

def calcular_resumen_perfil_kw_24h(
    perfil_kw_24h: Dict[int, float],
    consumo_mensual_referencia_kwh: float,
    dias_mes: int = 30,
) -> Dict[str, float]:
    """
    Calcula energía diaria, energía mensual estimada y consistencia
    contra el consumo mensual financiero de referencia.
    """

    validar_perfil_kw_24h(perfil_kw_24h)

    consumo_diario_kwh = sum(perfil_kw_24h.values())
    consumo_mensual_estimado_kwh = consumo_diario_kwh * dias_mes

    demanda_promedio_kw = consumo_diario_kwh / 24 if consumo_diario_kwh > 0 else 0.0
    demanda_maxima_kw = max(perfil_kw_24h.values()) if perfil_kw_24h else 0.0

    factor_carga = (
        demanda_promedio_kw / demanda_maxima_kw
        if demanda_maxima_kw > 0
        else 0.0
    )

    diferencia_kwh = consumo_mensual_estimado_kwh - consumo_mensual_referencia_kwh

    diferencia_pct = (
        diferencia_kwh / consumo_mensual_referencia_kwh * 100
        if consumo_mensual_referencia_kwh > 0
        else 0.0
    )

    return {
        "consumo_diario_kwh": consumo_diario_kwh,
        "consumo_mensual_estimado_kwh": consumo_mensual_estimado_kwh,
        "consumo_mensual_referencia_kwh": consumo_mensual_referencia_kwh,
        "diferencia_kwh": diferencia_kwh,
        "diferencia_pct": diferencia_pct,
        "demanda_promedio_kw": demanda_promedio_kw,
        "demanda_maxima_kw": demanda_maxima_kw,
        "factor_carga": factor_carga,
    }


def construir_consumo_horario_24h_kwh(
    perfil_kw_24h: Dict[int, float],
) -> Dict[int, float]:
    """
    Convierte perfil en kW promedio horario a energía horaria kWh.

    Como cada intervalo es de 1 hora:
    kW promedio = kWh del intervalo.
    """

    validar_perfil_kw_24h(perfil_kw_24h)

    return {
        hora: float(kw)
        for hora, kw in perfil_kw_24h.items()
    }


# ======================================================
# UI - PERFIL HORARIO
# ======================================================

def render_perfil_horario_tecnico(
    *,
    promedio_mensual: float,
) -> Tuple[Dict[int, float], Dict[int, float], Dict[str, float]]:
    """
    Renderiza la sección de perfil horario técnico.

    Retorna:
    - perfil_kw_24h
    - consumo_horario_24h_kwh
    - resumen_perfil
    """

    sf = st.session_state

    st.markdown("### Perfil horario técnico")

    st.caption(
        "Ingrese la potencia promedio estimada por hora. "
        "Cada valor en kW equivale al consumo de esa hora en kWh."
    )

    sf.setdefault("perfil_kw_24h", obtener_perfil_kw_24h())

    perfil_kw_24h = dict(sf["perfil_kw_24h"])

    cols_horas = st.columns(4)

    for hora in range(24):
        with cols_horas[hora % 4]:

            key = f"perfil_kw_hora_{hora}"

            if key not in sf:
                sf[key] = float(perfil_kw_24h.get(hora, 0.0))

            valor_kw = st.number_input(
                f"{hora:02d}:00 kW",
                key=key,
                min_value=0.0,
                step=0.5,
                format="%.2f",
            )

            perfil_kw_24h[hora] = float(valor_kw)

    sf["perfil_kw_24h"] = perfil_kw_24h

    consumo_horario_24h_kwh = construir_consumo_horario_24h_kwh(
        perfil_kw_24h=perfil_kw_24h,
    )

    resumen_perfil = calcular_resumen_perfil_kw_24h(
        perfil_kw_24h=perfil_kw_24h,
        consumo_mensual_referencia_kwh=promedio_mensual,
        dias_mes=30,
    )

    st.write(
        f"**Consumo diario estimado por perfil horario:** "
        f"{resumen_perfil['consumo_diario_kwh']:.2f} kWh/día"
    )

    st.write(
        f"**Consumo mensual estimado por perfil horario:** "
        f"{resumen_perfil['consumo_mensual_estimado_kwh']:.2f} kWh/mes"
    )

    st.write(
        f"**Consumo mensual financiero de referencia:** "
        f"{resumen_perfil['consumo_mensual_referencia_kwh']:.2f} kWh/mes"
    )

    st.write(
        f"**Diferencia:** "
        f"{resumen_perfil['diferencia_kwh']:.2f} kWh "
        f"({resumen_perfil['diferencia_pct']:.2f}%)"
    )

    st.write(
        f"**Demanda máxima horaria estimada:** "
        f"{resumen_perfil['demanda_maxima_kw']:.2f} kW"
    )

    st.write(
        f"**Factor de carga diario estimado:** "
        f"{resumen_perfil['factor_carga']:.2f}"
    )

    if abs(resumen_perfil["diferencia_pct"]) > 10:
        st.warning(
            "El perfil horario no es consistente con el consumo mensual. "
            "Revise los kW horarios o el consumo mensual ingresado."
        )
    else:
        st.success(
            "El perfil horario es razonablemente consistente con el consumo mensual."
        )

    with st.expander("Ver tabla del perfil horario"):
        st.dataframe(
            [
                {
                    "Hora": hora,
                    "Potencia promedio kW": perfil_kw_24h[hora],
                    "Energía horaria kWh": consumo_horario_24h_kwh[hora],
                }
                for hora in range(24)
            ],
            use_container_width=True,
        )

    return perfil_kw_24h, consumo_horario_24h_kwh, resumen_perfil


# ======================================================
# UI PRINCIPAL
# ======================================================

def render(ctx) -> None:
    """
    Paso 2: Captura consumo mensual, tarifa, cargos fijos
    y perfil horario técnico de consumo.

    Mantiene compatibilidad con variables previas:
    - ctx.consumo
    - ctx.consumo_12m
    - ctx.tarifa_energia
    - ctx.cargos_fijos
    """

    st.markdown("### Consumo energético")

    sf = st.session_state

    # ------------------------------------------------------
    # VALORES POR DEFECTO (SOLO PRIMERA VEZ)
    # ------------------------------------------------------
    sf.setdefault("kwh_12m", [18000.0] * 12)
    sf.setdefault("cargos_fijos_L_mes", 250.0)
    sf.setdefault("tarifa_energia_L_kwh", 5.50)

    consumo = {
        "kwh_12m": list(sf["kwh_12m"]),
        "cargos_fijos_L_mes": sf["cargos_fijos_L_mes"],
        "tarifa_energia_L_kwh": sf["tarifa_energia_L_kwh"],
        "fuente": "manual",
    }

    # ------------------------------------------------------
    # INPUTS MESES (3 COLUMNAS)
    # ------------------------------------------------------
    n_cols = 3
    cols = st.columns(n_cols)

    for i, mes in enumerate(_MESES):
        with cols[i % n_cols]:

            key = f"kwh_{i}"

            if key not in sf:
                sf[key] = consumo["kwh_12m"][i]

            val = st.number_input(
                f"{mes} (kWh)",
                key=key,
                min_value=0.0,
                step=0.1,
                format="%.2f",
            )

            consumo["kwh_12m"][i] = float(val)

    # ------------------------------------------------------
    # TARIFAS Y CARGOS
    # ------------------------------------------------------
    c1, c2 = st.columns(2)

    with c1:
        cargos = st.number_input(
            "Cargos fijos L/Mes",
            key="cargos_fijos_L_mes",
            min_value=0.0,
            step=1.0,
        )

    with c2:
        tarifa = st.number_input(
            "Tarifa energía L/kWh",
            key="tarifa_energia_L_kwh",
            min_value=0.0,
            step=0.01,
        )

    consumo["cargos_fijos_L_mes"] = float(cargos)
    consumo["tarifa_energia_L_kwh"] = float(tarifa)

    # ------------------------------------------------------
    # TOTALES FINANCIEROS
    # ------------------------------------------------------
    total_anual = sum(consumo["kwh_12m"])
    promedio_mensual = total_anual / 12 if total_anual > 0 else 0.0

    st.write(f"**Consumo anual total:** {total_anual:.2f} kWh")
    st.write(f"**Consumo promedio mensual:** {promedio_mensual:.2f} kWh")

    # ------------------------------------------------------
    # PERFIL HORARIO TÉCNICO
    # ------------------------------------------------------
    perfil_kw_24h, consumo_horario_24h_kwh, resumen_perfil = render_perfil_horario_tecnico(
        promedio_mensual=promedio_mensual,
    )

    # ------------------------------------------------------
    # GUARDAR EN CONTEXTO
    # ------------------------------------------------------
    ctx.consumo = consumo

    # Variables previas del sistema
    ctx.consumo_12m = consumo["kwh_12m"]
    ctx.tarifa_energia = consumo["tarifa_energia_L_kwh"]
    ctx.cargos_fijos = consumo["cargos_fijos_L_mes"]

    # Nuevas variables técnicas
    ctx.perfil_kw_24h = perfil_kw_24h
    ctx.consumo_horario_24h_kwh = consumo_horario_24h_kwh
    ctx.resumen_perfil_consumo = resumen_perfil


# ======================================================
# VALIDACIÓN
# ======================================================

def validar(ctx) -> Tuple[bool, List[str]]:
    """
    Valida que se hayan ingresado los 12 meses,
    al menos un consumo positivo y un perfil horario técnico válido.
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

    perfil_kw_24h = getattr(ctx, "perfil_kw_24h", {})

    try:
        validar_perfil_kw_24h(perfil_kw_24h)
    except Exception as exc:
        errores.append(str(exc))

    consumo_horario_24h_kwh = getattr(ctx, "consumo_horario_24h_kwh", {})

    if len(consumo_horario_24h_kwh) != 24:
        errores.append("El consumo horario técnico debe contener 24 horas.")

    if any(valor < 0 for valor in consumo_horario_24h_kwh.values()):
        errores.append("El consumo horario técnico no puede tener valores negativos.")

    return len(errores) == 0, errores
