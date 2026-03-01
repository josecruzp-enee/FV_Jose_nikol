# core/finanzas_lp.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .modelo import Datosproyecto
from .simular_12_meses import (
    simular_12_meses,
    calcular_cuota_mensual,
    om_mensual,
)
from .evaluacion import (
    evaluar_viabilidad,
    resumen_decision_mensual,
    payback_simple,
)


# ==========================================================
# Herramientas financieras base
# ==========================================================

def _npv(rate: float, cashflows: List[float]) -> float:
    r = float(rate)
    return sum(float(cf) / ((1.0 + r) ** t) for t, cf in enumerate(cashflows))


def _irr_bisection(
    cashflows: List[float],
    low: float = -0.9,
    high: float = 2.0,
    tol: float = 1e-7,
    max_iter: int = 300,
) -> Optional[float]:

    f_low = _npv(low, cashflows)
    f_high = _npv(high, cashflows)

    # Si no hay cruce de signo, intentar ampliar rango
    if f_low * f_high > 0:
        high = 5.0
        f_high = _npv(high, cashflows)
        if f_low * f_high > 0:
            return None

    a, b = low, high
    fa, fb = f_low, f_high

    for _ in range(max_iter):
        m = 0.5 * (a + b)
        fm = _npv(m, cashflows)

        if abs(fm) < tol:
            return m

        if fa * fm > 0:
            a, fa = m, fm
        else:
            b, fb = m, fm

    return 0.5 * (a + b)


def _payback_descontado_anios(rate: float, cashflows: List[float]) -> Optional[float]:
    r = float(rate)
    acumulado = 0.0

    for t, cf in enumerate(cashflows):
        pv = float(cf) / ((1.0 + r) ** t)
        anterior = acumulado
        acumulado += pv

        if t == 0:
            continue

        if acumulado >= 0:
            delta = acumulado - anterior
            frac = (0 - anterior) / delta if abs(delta) > 1e-12 else 0.0
            return (t - 1) + frac

    return None


# ==========================================================
# Motor financiero completo
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

    # ------------------------------------------------------
    # 1️⃣ Extraer datos técnicos necesarios
    # ------------------------------------------------------
    kwp_dc = float(sizing.get("kwp_dc") or sizing.get("pdc_kw") or 0.0)
    capex = float(sizing.get("capex_L") or 0.0)

    if kwp_dc <= 0 or capex <= 0:
        raise ValueError("Sizing incompleto para ejecutar finanzas.")

    # ------------------------------------------------------
    # 2️⃣ Cuota mensual
    # ------------------------------------------------------
    cuota_mensual = calcular_cuota_mensual(
        capex_L_=capex,
        tasa_anual=float(datos.tasa_anual),
        plazo_anios=int(datos.plazo_anios),
        pct_fin=float(datos.porcentaje_financiado),
    )

    # ------------------------------------------------------
    # 3️⃣ Simulación 12 meses
    # ------------------------------------------------------
    tabla_12m = simular_12_meses(datos, kwp_dc, cuota_mensual, capex)

    # ------------------------------------------------------
    # 4️⃣ Evaluación mensual
    # ------------------------------------------------------
    evaluacion = evaluar_viabilidad(tabla_12m, cuota_mensual)
    decision = resumen_decision_mensual(tabla_12m, cuota_mensual, datos)

    ahorro_anual = sum(float(x.get("ahorro_L", 0.0)) for x in tabla_12m)
    payback_simple_anios = payback_simple(capex, ahorro_anual)

    # ------------------------------------------------------
    # 5️⃣ Proyección financiera larga
    # ------------------------------------------------------
    om_pct = float(getattr(datos, "om_anual_pct", 0.0))
    om_y1 = om_mensual(capex, om_pct) * 12.0
    pago_cuota_y1 = cuota_mensual * 12.0

    pago_base_y1 = sum(float(r["factura_base_L"]) for r in tabla_12m)
    pago_residual_y1 = sum(float(r["pago_enee_L"]) for r in tabla_12m)

    fv_util_kwh_y1 = sum(float(r["fv_kwh"]) for r in tabla_12m)
    cons_kwh_y1 = sum(float(r["consumo_kwh"]) for r in tabla_12m)

    cashflows = [-capex]
    tabla_anual = []

    for anio in range(1, horizonte_anios + 1):

        f_tar = (1.0 + crecimiento_tarifa_anual) ** (anio - 1)
        f_deg = (1.0 - degradacion_fv_anual) ** (anio - 1)

        pago_base = pago_base_y1 * f_tar
        pago_residual = pago_residual_y1 * f_tar * f_deg

        ahorro = pago_base - pago_residual

        pagos_cuota = pago_cuota_y1 if anio <= int(datos.plazo_anios) else 0.0

        reemplazo = 0.0
        if reemplazo_inversor_anio and anio == reemplazo_inversor_anio:
            reemplazo = reemplazo_inversor_pct_capex * capex

        flujo_neto = ahorro - pagos_cuota - om_y1 - reemplazo

        tabla_anual.append({
            "anio": anio,
            "ahorro_L": ahorro,
            "pago_cuota_L": pagos_cuota,
            "om_L": om_y1,
            "reemplazo_L": reemplazo,
            "flujo_neto_L": flujo_neto,
        })

        cashflows.append(flujo_neto)

    npv = _npv(tasa_descuento, cashflows)
    irr = _irr_bisection(cashflows)
    payback_desc = _payback_descontado_anios(tasa_descuento, cashflows)

    finanzas_lp = {
        "supuestos": {
            "horizonte_anios": horizonte_anios,
            "crecimiento_tarifa_anual": crecimiento_tarifa_anual,
            "degradacion_fv_anual": degradacion_fv_anual,
            "tasa_descuento": tasa_descuento,
            "reemplazo_inversor_anio": reemplazo_inversor_anio,
            "reemplazo_inversor_pct_capex": reemplazo_inversor_pct_capex,
        },
        "cashflows": cashflows,
        "tabla_anual": tabla_anual,
        "npv_L": float(npv),
        "irr": None if irr is None else float(irr),
        "payback_descontado_anios": payback_desc,
    }

    # ------------------------------------------------------
    # 6️⃣ Retorno consolidado financiero
    # ------------------------------------------------------
    return {
        "cuota_mensual": cuota_mensual,
        "tabla_12m": tabla_12m,
        "evaluacion": evaluacion,
        "decision": decision,
        "ahorro_anual_L": ahorro_anual,
        "payback_simple_anios": payback_simple_anios,
        "finanzas_lp": finanzas_lp,
    }
