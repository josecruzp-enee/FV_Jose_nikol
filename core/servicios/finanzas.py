from __future__ import annotations

from typing import Any, Dict, List

from core.dominio.modelo import Datosproyecto
from core.dominio.contrato import ResultadoSizing
from energy.resultado_energia import EnergiaResultado

def _normalizar_energia(energia):

    if not isinstance(energia, list):
        raise ValueError("energia debe ser lista")

    resultado = []

    for x in energia:

        # caso 1: número directo
        if isinstance(x, (int, float)):
            resultado.append(float(x))
            continue

        # caso 2: dict
        if isinstance(x, dict):

            if "valor" in x:
                resultado.append(float(x["valor"]))
                continue

            if "energia" in x:
                resultado.append(float(x["energia"]))
                continue

            if "energia_kwh" in x:  # 🔥 ESTE ES TU CASO REAL
                resultado.append(float(x["energia_kwh"]))
                continue

        raise ValueError(f"Formato inválido en energía: {x}")

    return resultado
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
# 🔵 SIMULACIÓN OPERATIVA MENSUAL
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

    energia_fv_12m = _normalizar_energia(energia_fv_12m)
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

def _evaluacion_mensual(tabla: list, cuota: float) -> dict:

    if not tabla or len(tabla) == 0:
        return {
            "estado": "ERROR",
            "nota": "Tabla financiera vacía",
            "dscr": None,
            "ahorro_prom": 0.0,
            "neto_prom": 0.0,
            "peor_mes": 0.0,
        }

    ahorros = [x.get("ahorro_L", 0.0) for x in tabla]
    netos = [x.get("neto_L", 0.0) for x in tabla]
    oms = [x.get("om_L", 0.0) for x in tabla]

    ahorro_prom = sum(ahorros) / len(ahorros)
    neto_prom = sum(netos) / len(netos)
    peor_mes = min(netos)
    om_prom = sum(oms) / len(oms)

    deuda_mensual = cuota + om_prom

    # ======================================================
    # DSCR (CORREGIDO)
    # ======================================================
    if deuda_mensual > 0:
        dscr = ahorro_prom / deuda_mensual
    else:
        dscr = None  # 🔥 sistema sin financiamiento

    # ======================================================
    # ESTADO (ROBUSTO)
    # ======================================================
    if dscr is None:
        estado = "SIN FINANCIAMIENTO"
        nota = "Sistema evaluado sin deuda (flujo directo)."

    elif dscr >= 1.20 and peor_mes >= 0:
        estado = "VIABLE"
        nota = "Excelente cobertura financiera. Flujo positivo en todos los meses."

    elif dscr >= 1.00:
        estado = "ACEPTABLE"
        nota = "Sistema sostenible. Flujo cercano al equilibrio."

    elif dscr >= 0.80:
        estado = "MARGINAL"
        nota = "Riesgo moderado. Algunos meses pueden ser ajustados."

    else:
        estado = "NO VIABLE"
        nota = "Los ahorros no cubren adecuadamente la deuda."

    return {
        "estado": estado,
        "nota": nota,
        "dscr": dscr,
        "ahorro_prom": ahorro_prom,
        "neto_prom": neto_prom,
        "peor_mes": peor_mes,
    }


# ==========================================================
# 🔵 TIR
# ==========================================================

def _tir(flujos, guess=0.1):
    r = guess
    for _ in range(100):
        vpn = sum(f / (1 + r) ** i for i, f in enumerate(flujos))
        deriv = sum(-i * f / (1 + r) ** (i + 1) for i, f in enumerate(flujos))
        if abs(deriv) < 1e-10:
            break
        r -= vpn / deriv
    return r


# ==========================================================
# 🔵 ENTRYPOINT FINANCIERO
# ==========================================================

def ejecutar_finanzas(
    *,
    datos: Datosproyecto,
    sizing: ResultadoSizing,
    energia: EnergiaResultado,
) -> Dict[str, Any]:

    kwp_dc = float(sizing.pdc_kw)

    if kwp_dc <= 0:
        raise ValueError("Sizing incompleto para finanzas.")

    if energia is None:
        raise ValueError("Resultado energético no definido.")

    if not energia.ok:
        raise ValueError(f"Energía inválida: {energia.errores}")

    energia_fv_12m = getattr(energia, "energia_util_12m", None)

    if not energia_fv_12m or len(energia_fv_12m) != 12:
        raise ValueError("Energía mensual inválida.")

    capex = calcular_capex_L(
        pdc_kw=kwp_dc,
        costo_usd_kwp=datos.costo_usd_kwp,
        tcambio=datos.tcambio,
    )

    cuota = calcular_cuota_mensual(
        capex_L_=capex,
        tasa_anual=datos.tasa_anual,
        plazo_anios=datos.plazo_anios,
        pct_fin=datos.porcentaje_financiado,
    )

    om_mensual_val = om_mensual(capex, datos.om_anual_pct)

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

    # ==========================================================
    # 🔥 INDICADORES FINANCIEROS
    # ==========================================================

    roi = (ahorro_anual / capex) * 100 if capex > 0 else 0.0
    payback = capex / ahorro_anual if ahorro_anual > 0 else 0.0

    flujos = [-capex]
    for _ in range(10):
        flujos.append(ahorro_anual)

    tir = _tir(flujos) * 100

    return {
        "capex_L": capex,
        "cuota_mensual": cuota,
        "tabla_12m": tabla_12m,
        "evaluacion": evaluacion,
        "ahorro_anual_L": ahorro_anual,
        "roi_pct": roi,
        "payback_anios": payback,
        "tir_pct": tir,
    }
