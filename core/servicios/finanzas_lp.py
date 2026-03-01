from __future__ import annotations

from typing import Any, Dict, List

from .modelo import Datosproyecto
from electrical.energia.contrato import EnergiaResultado


# ==========================================================
# 🔵 CAPEX
# ==========================================================

def calcular_capex_L(
    pdc_kw: float,
    costo_usd_kwp: float,
    tcambio: float,
) -> float:
    return float(pdc_kw) * float(costo_usd_kwp) * float(tcambio)


# ==========================================================
# 🔵 Funciones financieras básicas
# ==========================================================

def calcular_cuota_mensual(
    capex_L_: float,
    tasa_anual: float,
    plazo_anios: int,
    pct_fin: float,
) -> float:

    principal = float(capex_L_) * float(pct_fin)
    r = float(tasa_anual) / 12.0
    n = int(plazo_anios) * 12

    if n <= 0:
        raise ValueError("Plazo inválido.")

    if abs(r) < 1e-12:
        return principal / n

    return (r * principal) / (1 - (1 + r) ** (-n))


def om_mensual(capex_L_: float, om_anual_pct: float) -> float:
    return (float(om_anual_pct) * float(capex_L_)) / 12.0


# ==========================================================
# 🔵 SIMULACIÓN OPERATIVA MENSUAL (YA NO CALCULA ENERGÍA)
# ==========================================================

def simular_12_meses(
    *,
    consumo_12m: List[float],
    energia_fv_12m: List[float],
    tarifa_energia: float,
    cargos_fijos: float,
    cuota_mensual: float,
    om_mensual_val: float,
) -> List[Dict[str, float]]:

    if len(consumo_12m) != 12:
        raise ValueError("consumo_12m debe tener 12 valores")

    if len(energia_fv_12m) != 12:
        raise ValueError("energia_fv_12m debe tener 12 valores")

    tabla: List[Dict[str, float]] = []

    for i in range(12):

        consumo = float(consumo_12m[i])
        gen_real = float(energia_fv_12m[i])

        gen_util = min(consumo, gen_real)
        kwh_enee = consumo - gen_util

        factura_base = consumo * float(tarifa_energia) + float(cargos_fijos)
        pago_enee = kwh_enee * float(tarifa_energia) + float(cargos_fijos)

        ahorro = factura_base - pago_enee
        neto = ahorro - float(cuota_mensual) - float(om_mensual_val)

        tabla.append({
            "mes": i + 1,
            "consumo_kwh": consumo,
            "fv_kwh": gen_util,
            "kwh_enee": kwh_enee,
            "factura_base_L": factura_base,
            "pago_enee_L": pago_enee,
            "ahorro_L": ahorro,
            "cuota_L": float(cuota_mensual),
            "om_L": float(om_mensual_val),
            "neto_L": neto,
        })

    return tabla


# ==========================================================
# 🔵 Evaluación mensual
# ==========================================================

def _evaluacion_mensual(tabla: List[Dict[str, float]], cuota: float) -> Dict[str, Any]:

    ahorros = [x["ahorro_L"] for x in tabla]
    netos = [x["neto_L"] for x in tabla]
    oms = [x["om_L"] for x in tabla]

    ahorro_prom = sum(ahorros) / len(ahorros)
    neto_prom = sum(netos) / len(netos)
    peor_mes = min(netos)
    om_prom = sum(oms) / len(oms)

    dscr = (ahorro_prom - om_prom) / cuota if cuota > 0 else 0.0

    if dscr >= 1.2 and peor_mes >= 0:
        estado = "VIABLE"
        nota = "Se paga cómodamente y no hay meses negativos."
    elif dscr >= 1.0:
        estado = "MARGINAL"
        nota = "Se sostiene en promedio."
    else:
        estado = "NO VIABLE"
        nota = "Los ahorros no cubren bien la cuota."

    return {
        "estado": estado,
        "nota": nota,
        "dscr": dscr,
        "ahorro_prom": ahorro_prom,
        "neto_prom": neto_prom,
        "peor_mes": peor_mes,
    }


# ==========================================================
# 🔵 ENTRYPOINT FINANCIERO (YA USA MOTOR ENERGÉTICO REAL)
# ==========================================================

def ejecutar_finanzas(
    *,
    datos: Datosproyecto,
    sizing: Dict[str, Any],
    energia: EnergiaResultado,
) -> Dict[str, Any]:

    kwp_dc = float(sizing.get("pdc_kw") or 0.0)

    if kwp_dc <= 0:
        raise ValueError("Sizing incompleto para finanzas.")

    if not energia.ok:
        raise ValueError("Motor energético inválido.")

    # CAPEX
    capex = calcular_capex_L(
        pdc_kw=kwp_dc,
        costo_usd_kwp=datos.costo_usd_kwp,
        tcambio=datos.tcambio,
    )

    # Deuda
    cuota = calcular_cuota_mensual(
        capex_L_=capex,
        tasa_anual=datos.tasa_anual,
        plazo_anios=datos.plazo_anios,
        pct_fin=datos.porcentaje_financiado,
    )

    om_mensual_val = om_mensual(capex, datos.om_anual_pct)

    # Energía real mensual (ya física)
    energia_fv_12m = energia.energia_util_12m

    # Simulación
    tabla_12m = simular_12_meses(
        consumo_12m=datos.consumo_12m,
        energia_fv_12m=energia_fv_12m,
        tarifa_energia=datos.tarifa_energia,
        cargos_fijos=datos.cargos_fijos,
        cuota_mensual=cuota,
        om_mensual_val=om_mensual_val,
    )

    evaluacion = _evaluacion_mensual(tabla_12m, cuota)
    ahorro_anual = sum(x["ahorro_L"] for x in tabla_12m)

    return {
        "capex_L": capex,
        "cuota_mensual": cuota,
        "tabla_12m": tabla_12m,
        "evaluacion": evaluacion,
        "ahorro_anual_L": ahorro_anual,
    }
