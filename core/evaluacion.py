# nucleo/evaluacion.py
from __future__ import annotations

from typing import Any, Dict, List

from .modelo import Datosproyecto


def promedio(vals: List[float]) -> float:
    return (sum(vals) / len(vals)) if vals else 0.0


def peor_mes(vals: List[float]) -> float:
    return min(vals) if vals else 0.0


def dscr(ahorro_prom: float, om_prom: float, cuota: float) -> float:
    return (ahorro_prom - om_prom) / cuota if cuota > 0 else 0.0


def dictamen(dscr_: float, peor_mes_neto: float) -> Dict[str, str]:
    if dscr_ >= 1.2 and peor_mes_neto >= 0:
        return {"estado": "✅ VIABLE", "nota": "Se paga cómodamente y no hay meses negativos."}
    if dscr_ >= 1.0:
        return {"estado": "⚠️ MARGINAL", "nota": "Se sostiene en promedio, pero hay meses con flujo bajo/negativo."}
    return {"estado": "❌ NO VIABLE", "nota": "Los ahorros no cubren bien la cuota; ajustar tamaño/plazo/costo."}


def evaluar_viabilidad(tabla: List[Dict[str, float]], cuota_mensual_: float) -> Dict[str, Any]:
    ahorros = [x["ahorro_L"] for x in tabla]
    netos = [x["neto_L"] for x in tabla]
    oms = [x["om_L"] for x in tabla]

    ahorro_prom = promedio(ahorros)
    neto_prom = promedio(netos)
    peor = peor_mes(netos)
    om_prom = promedio(oms)

    ds = dscr(ahorro_prom, om_prom, float(cuota_mensual_))
    d = dictamen(ds, peor)

    return {
        "estado": d["estado"],
        "nota": d["nota"],
        "dscr": ds,
        "ahorro_prom": ahorro_prom,
        "neto_prom": neto_prom,
        "peor_mes": peor,
    }


def resumen_decision_mensual(tabla_12m: List[Dict[str, float]], cuota_mensual_: float, p: Datosproyecto) -> Dict[str, float]:
    pago_actual_total = 0.0
    pago_residual_total = 0.0

    for f in tabla_12m:
        consumo = float(f["consumo_kwh"])
        pago_actual_total += consumo * float(p.tarifa_energia) + float(p.cargos_fijos)
        pago_residual_total += float(f["pago_enee_L"])

    pago_actual = pago_actual_total / 12.0
    pago_residual = pago_residual_total / 12.0
    pago_total_fv = pago_residual + float(cuota_mensual_)
    ahorro_mensual_ = pago_actual - pago_total_fv

    return {
        "pago_actual": pago_actual,
        "pago_residual": pago_residual,
        "cuota": float(cuota_mensual_),
        "pago_total_fv": pago_total_fv,
        "ahorro_mensual": ahorro_mensual_,
        "pago_post_fv": pago_residual,
    }


def payback_simple(capex_L_: float, ahorro_anual_L_: float) -> float:
    return (float(capex_L_) / float(ahorro_anual_L_)) if ahorro_anual_L_ > 0 else float("inf")
