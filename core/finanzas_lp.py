# core/finanzas_lp.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .modelo import Datosproyecto
from .simular_12_meses import (
    simular_12_meses,
    calcular_cuota_mensual,
    om_mensual,
)


# ==========================================================
# Utilidades matemáticas base
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
# Evaluación mensual
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
        estado = "✅ VIABLE"
        nota = "Se paga cómodamente y no hay meses negativos."
    elif dscr >= 1.0:
        estado = "⚠️ MARGINAL"
        nota = "Se sostiene en promedio, pero hay meses con flujo bajo/negativo."
    else:
        estado = "❌ NO VIABLE"
        nota = "Los ahorros no cubren bien la cuota; ajustar tamaño/plazo/costo."

    return {
        "estado": estado,
        "nota": nota,
        "dscr": dscr,
        "ahorro_prom": ahorro_prom,
        "neto_prom": neto_prom,
        "peor_mes": peor_mes,
    }


def _resumen_mensual(tabla: List[Dict[str, float]], cuota: float, p: Datosproyecto) -> Dict[str, float]:
    pago_actual = 0.0
    pago_residual = 0.0

    for f in tabla:
        consumo = f["consumo_kwh"]
        pago_actual += consumo * p.tarifa_energia + p.cargos_fijos
        pago_residual += f["pago_enee_L"]

    pago_actual /= 12.0
    pago_residual /= 12.0

    pago_total_fv = pago_residual + cuota
    ahorro_mensual = pago_actual - pago_total_fv

    return {
        "pago_actual": pago_actual,
        "pago_residual": pago_residual,
        "cuota": cuota,
        "pago_total_fv": pago_total_fv,
        "ahorro_mensual": ahorro_mensual,
        "pago_post_fv": pago_residual,
    }


def _payback_simple(capex: float, ahorro_anual: float) -> float:
    return capex / ahorro_anual if ahorro_anual > 0 else float("inf")


# ==========================================================
# Proyección financiera larga
# ==========================================================

def _proyeccion_larga(
    *,
    datos: Datosproyecto,
    capex: float,
    cuota: float,
    tabla_12m: List[Dict[str, float]],
    horizonte: int,
    crecimiento_tarifa: float,
    degradacion_fv: float,
    tasa_descuento: float,
    reemplazo_anio: Optional[int],
    reemplazo_pct: float,
) -> Dict[str, Any]:

    om_y1 = om_mensual(capex, getattr(datos, "om_anual_pct", 0.0)) * 12
    pago_cuota_y1 = cuota * 12

    pago_base_y1 = sum(r["factura_base_L"] for r in tabla_12m)
    pago_residual_y1 = sum(r["pago_enee_L"] for r in tabla_12m)

    cashflows = [-capex]
    tabla_anual = []

    for anio in range(1, horizonte + 1):
        f_tar = (1 + crecimiento_tarifa) ** (anio - 1)
        f_deg = (1 - degradacion_fv) ** (anio - 1)

        pago_base = pago_base_y1 * f_tar
        pago_residual = pago_residual_y1 * f_tar * f_deg
        ahorro = pago_base - pago_residual

        cuota_anual = pago_cuota_y1 if anio <= datos.plazo_anios else 0.0
        reemplazo = reemplazo_pct * capex if reemplazo_anio and anio == reemplazo_anio else 0.0

        flujo = ahorro - cuota_anual - om_y1 - reemplazo

        tabla_anual.append({
            "anio": anio,
            "ahorro_L": ahorro,
            "flujo_neto_L": flujo,
        })

        cashflows.append(flujo)

    return {
        "cashflows": cashflows,
        "tabla_anual": tabla_anual,
        "npv_L": _npv(tasa_descuento, cashflows),
        "irr": _irr_bisection(cashflows),
        "payback_descontado_anios": _payback_descontado(tasa_descuento, cashflows),
    }


# ==========================================================
# ENTRYPOINT ÚNICO
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

    kwp_dc = float(sizing.get("kwp_dc") or sizing.get("pdc_kw") or 0.0)
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
    decision = _resumen_mensual(tabla_12m, cuota, datos)

    ahorro_anual = sum(x["ahorro_L"] for x in tabla_12m)
    pb_simple = _payback_simple(capex, ahorro_anual)

    finanzas_lp = _proyeccion_larga(
        datos=datos,
        capex=capex,
        cuota=cuota,
        tabla_12m=tabla_12m,
        horizonte=horizonte_anios,
        crecimiento_tarifa=crecimiento_tarifa_anual,
        degradacion_fv=degradacion_fv_anual,
        tasa_descuento=tasa_descuento,
        reemplazo_anio=reemplazo_inversor_anio,
        reemplazo_pct=reemplazo_inversor_pct_capex,
    )

    return {
        "cuota_mensual": cuota,
        "tabla_12m": tabla_12m,
        "evaluacion": evaluacion,
        "decision": decision,
        "ahorro_anual_L": ahorro_anual,
        "payback_simple_anios": pb_simple,
        "finanzas_lp": finanzas_lp,
    }
