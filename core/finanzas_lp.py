# nucleo/finanzas_lp.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .modelo import Datosproyecto
from modelo.simulacion_12m import om_mensual


def _npv(rate: float, cashflows: List[float]) -> float:
    r = float(rate)
    out = 0.0
    for t, cf in enumerate(cashflows):
        out += float(cf) / ((1.0 + r) ** t)
    return out


def _irr_bisection(
    cashflows: List[float],
    low: float = -0.9,
    high: float = 1.5,
    tol: float = 1e-7,
    max_iter: int = 200
) -> Optional[float]:
    f_low = _npv(low, cashflows)
    f_high = _npv(high, cashflows)

    if f_low == 0.0:
        return low
    if f_high == 0.0:
        return high
    if (f_low > 0 and f_high > 0) or (f_low < 0 and f_high < 0):
        return None

    a, b = low, high
    fa, fb = f_low, f_high
    for _ in range(max_iter):
        m = 0.5 * (a + b)
        fm = _npv(m, cashflows)
        if abs(fm) < tol:
            return m
        if (fa > 0 and fm > 0) or (fa < 0 and fm < 0):
            a, fa = m, fm
        else:
            b, fb = m, fm
    return 0.5 * (a + b)


def _payback_descontado_anios(rate: float, cashflows: List[float]) -> Optional[float]:
    r = float(rate)
    acum = 0.0
    for t, cf in enumerate(cashflows):
        pv = float(cf) / ((1.0 + r) ** t)
        prev = acum
        acum += pv
        if t == 0:
            continue
        if acum >= 0:
            delta = acum - prev
            frac = (0 - prev) / delta if abs(delta) > 1e-12 else 0.0
            return (t - 1) + frac
    return None


def proyectar_flujos_anuales(
    *,
    datos: Datosproyecto,
    resultado: Dict[str, Any],
    horizonte_anios: int = 15,
    crecimiento_tarifa_anual: float = 0.06,
    degradacion_fv_anual: float = 0.006,
    tasa_descuento: float = 0.14,
    reemplazo_inversor_anio: Optional[int] = 12,
    reemplazo_inversor_pct_capex: float = 0.15,
) -> Dict[str, Any]:
    sz = resultado["sizing"]
    tabla_12m = resultado["tabla_12m"]

    capex = float(sz["capex_L"])
    cuota_m = float(resultado["cuota_mensual"])
    om_pct = float(getattr(datos, "om_anual_pct", 0.0))

    ahorro_y1 = sum(float(r["ahorro_L"]) for r in tabla_12m)
    om_y1 = om_mensual(capex, om_pct) * 12.0
    pago_cuota_y1 = cuota_m * 12.0

    cons_kwh_y1 = sum(float(r["consumo_kwh"]) for r in tabla_12m)
    fv_util_kwh_y1 = sum(float(r["fv_kwh"]) for r in tabla_12m)

    pago_base_y1 = sum(float(r["factura_base_L"]) for r in tabla_12m)
    pago_residual_y1 = sum(float(r["pago_enee_L"]) for r in tabla_12m)

    cashflows = [-capex]
    tabla_anual = []

    for anio in range(1, int(horizonte_anios) + 1):
        f_tar = (1.0 + float(crecimiento_tarifa_anual)) ** (anio - 1)
        f_deg = (1.0 - float(degradacion_fv_anual)) ** (anio - 1)

        fv_kwh = fv_util_kwh_y1 * f_deg
        cons_kwh = cons_kwh_y1

        ahorro = ahorro_y1 * f_tar * f_deg
        om = om_y1
        pagos_cuota = pago_cuota_y1 if anio <= int(datos.plazo_anios) else 0.0

        reemplazo = 0.0
        if reemplazo_inversor_anio is not None and anio == int(reemplazo_inversor_anio):
            reemplazo = float(reemplazo_inversor_pct_capex) * capex

        flujo_neto = ahorro - pagos_cuota - om - reemplazo

        tabla_anual.append({
            "anio": anio,
            "consumo_kwh": cons_kwh,
            "fv_util_kwh": fv_kwh,
            "factor_tarifa": f_tar,
            "factor_degrad": f_deg,
            "ahorro_L": ahorro,
            "pago_cuota_L": pagos_cuota,
            "om_L": om,
            "reemplazo_L": reemplazo,
            "flujo_neto_L": flujo_neto,
        })
        cashflows.append(flujo_neto)

    npv = _npv(float(tasa_descuento), cashflows)
    irr = _irr_bisection(cashflows)
    pb_desc = _payback_descontado_anios(float(tasa_descuento), cashflows)

    return {
        "supuestos": {
            "horizonte_anios": int(horizonte_anios),
            "crecimiento_tarifa_anual": float(crecimiento_tarifa_anual),
            "degradacion_fv_anual": float(degradacion_fv_anual),
            "tasa_descuento": float(tasa_descuento),
            "reemplazo_inversor_anio": reemplazo_inversor_anio,
            "reemplazo_inversor_pct_capex": float(reemplazo_inversor_pct_capex),
        },
        "baselines_y1": {
            "ahorro_anual_L": float(ahorro_y1),
            "om_anual_L": float(om_y1),
            "pago_cuota_anual_L": float(pago_cuota_y1),
            "pago_base_anual_L": float(pago_base_y1),
            "pago_residual_anual_L": float(pago_residual_y1),
            "consumo_anual_kwh": float(cons_kwh_y1),
            "fv_util_anual_kwh": float(fv_util_kwh_y1),
        },
        "cashflows": cashflows,
        "tabla_anual": tabla_anual,
        "npv_L": float(npv),
        "irr": None if irr is None else float(irr),
        "payback_descontado_anios": pb_desc,
    }
