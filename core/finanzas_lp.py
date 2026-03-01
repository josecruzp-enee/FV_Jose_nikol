# core/finanzas_lp.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .modelo import Datosproyecto
from .simular_12_meses import simular_12_meses


# ==========================================================
# 🔵 Funciones financieras básicas (MOVIDAS)
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
# 🔵 Utilidades matemáticas base
# ==========================================================

def _npv(rate: float, cashflows: List[float]) -> float:
    return sum(cf / ((1.0 + rate) ** t) for t, cf in enumerate(cashflows))


def _irr_bisection(cashflows: List[float]) -> Optional[float]:
    low, high = -0.9, 2.0
    f_low = _npv(low, cashflows)
    f_high = _npv(high, cashflows)

    if f_low * f_high > 0:
        high = 5.0
        f_high = _npv(high, cashflows)
        if f_low * f_high > 0:
            return None

    for _ in range(300):
        mid = (low + high) / 2
        f_mid = _npv(mid, cashflows)

        if abs(f_mid) < 1e-7:
            return mid

        if f_low * f_mid > 0:
            low, f_low = mid, f_mid
        else:
            high, f_high = mid, f_mid

    return (low + high) / 2


def _payback_descontado(rate: float, cashflows: List[float]) -> Optional[float]:
    acumulado = 0.0

    for t, cf in enumerate(cashflows):
        pv = cf / ((1.0 + rate) ** t)
        anterior = acumulado
        acumulado += pv

        if t > 0 and acumulado >= 0:
            delta = acumulado - anterior
            frac = (0 - anterior) / delta if abs(delta) > 1e-12 else 0.0
            return (t - 1) + frac

    return None


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
        nota = "Se sostiene en promedio, pero hay meses con flujo bajo/negativo."
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
# 🔵 ENTRYPOINT
# ==========================================================

def ejecutar_finanzas(
    *,
    datos: Datosproyecto,
    sizing: Dict[str, Any],
    horizonte_anios: int = 15,
    crecimiento_tarifa_anual: float = 0.06,
    degradacion_fv_anual: float = 0.006,
    tasa_descuento: float = 0.14,
    reemplazo_inversor_anio: Optional[int] = 12,
    reemplazo_inversor_pct_capex: float = 0.15,
) -> Dict[str, Any]:

    kwp_dc = float(sizing.get("pdc_kw") or 0.0)
    capex = float(sizing.get("capex_L") or 0.0)

    if kwp_dc <= 0 or capex <= 0:
        raise ValueError("Sizing incompleto para finanzas.")

    cuota = calcular_cuota_mensual(
        capex_L_=capex,
        tasa_anual=datos.tasa_anual,
        plazo_anios=datos.plazo_anios,
        pct_fin=datos.porcentaje_financiado,
    )

    tabla_12m = simular_12_meses(datos, kwp_dc, cuota, capex)

    evaluacion = _evaluacion_mensual(tabla_12m, cuota)

    ahorro_anual = sum(x["ahorro_L"] for x in tabla_12m)

    return {
        "cuota_mensual": cuota,
        "tabla_12m": tabla_12m,
        "evaluacion": evaluacion,
        "ahorro_anual_L": ahorro_anual,
    }
