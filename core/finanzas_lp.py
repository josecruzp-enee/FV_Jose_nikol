from __future__ import annotations

from typing import Any, Dict, List, Optional

from .modelo import Datosproyecto
from .simulacion_12m import simular_12_meses


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
# 🔵 ENTRYPOINT FINANCIERO
# ==========================================================

def ejecutar_finanzas(
    *,
    datos: Datosproyecto,
    sizing: Dict[str, Any],
) -> Dict[str, Any]:

    kwp_dc = float(sizing.get("pdc_kw") or 0.0)

    if kwp_dc <= 0:
        raise ValueError("Sizing incompleto para finanzas.")

    # --------------------------
    # CAPEX
    # --------------------------

    capex = calcular_capex_L(
        pdc_kw=kwp_dc,
        costo_usd_kwp=datos.costo_usd_kwp,
        tcambio=datos.tcambio,
    )

    # --------------------------
    # Cuota
    # --------------------------

    cuota = calcular_cuota_mensual(
        capex_L_=capex,
        tasa_anual=datos.tasa_anual,
        plazo_anios=datos.plazo_anios,
        pct_fin=datos.porcentaje_financiado,
    )

    om_mensual_val = om_mensual(
        capex_L_=capex,
        om_anual_pct=datos.om_anual_pct,
    )

    # --------------------------
    # Parámetros energéticos (desde sistema_fv ya validado)
    # --------------------------

    sfv = getattr(datos, "sistema_fv", {}) or {}

    prod_base = float(sfv.get("prod_base_kwh_kwp_mes") or 0.0)
    factores_12m = sfv.get("factores_fv_12m") or [1.0] * 12
    factor_orientacion = float(sfv.get("factor_orientacion") or 1.0)

    # --------------------------
    # Simulación mensual pura
    # --------------------------

    tabla_12m = simular_12_meses(
        consumo_12m=datos.consumo_12m,
        factores_12m=factores_12m,
        tarifa_energia=datos.tarifa_energia,
        cargos_fijos=datos.cargos_fijos,
        prod_base_kwh_kwp_mes=prod_base,
        kwp=kwp_dc,
        cuota_mensual=cuota,
        om_mensual_val=om_mensual_val,
        factor_orientacion=factor_orientacion,
    )

    # --------------------------
    # Evaluación
    # --------------------------

    evaluacion = _evaluacion_mensual(tabla_12m, cuota)

    ahorro_anual = sum(x["ahorro_L"] for x in tabla_12m)

    return {
        "capex_L": capex,
        "cuota_mensual": cuota,
        "tabla_12m": tabla_12m,
        "evaluacion": evaluacion,
        "ahorro_anual_L": ahorro_anual,
    }
