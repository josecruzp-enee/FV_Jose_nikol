from __future__ import annotations

from typing import Any, Dict, List

from core.dominio.modelo import Datosproyecto
from core.dominio.contrato import ResultadoSizing
from energy.resultado_energia import EnergiaResultado
from energy.baterias import ConfigBateria, ejecutar_bateria


def _normalizar_energia(energia):

    if not isinstance(energia, list):
        raise ValueError("energia debe ser lista")

    resultado = []

    for x in energia:

        if isinstance(x, (int, float)):
            resultado.append(float(x))
            continue

        if isinstance(x, dict):

            if "valor" in x:
                resultado.append(float(x["valor"]))
                continue

            if "energia" in x:
                resultado.append(float(x["energia"]))
                continue

            if "energia_kwh" in x:
                resultado.append(float(x["energia_kwh"]))
                continue

        raise ValueError(f"Formato inválido en energía: {x}")

    return resultado


def _extraer_valor_bateria(resultado_bateria, nombres, default=0.0) -> float:
    for nombre in nombres:
        valor = getattr(resultado_bateria, nombre, None)

        if valor is None and isinstance(resultado_bateria, dict):
            valor = resultado_bateria.get(nombre)

        if valor is not None:
            try:
                return float(valor or 0.0)
            except Exception:
                pass

    return float(default)


def _energia_descargada_bateria_diaria(resultado_bateria) -> float:
    valor_directo = _extraer_valor_bateria(
        resultado_bateria,
        [
            "energia_descargada_kwh",
            "energia_entregada_kwh",
            "energia_util_bateria_kwh",
            "energia_bateria_kwh",
            "descarga_total_kwh",
            "descargada_kwh",
        ],
        0.0,
    )

    if valor_directo > 0:
        return valor_directo

    descarga_24h = getattr(resultado_bateria, "descarga_24h_kwh", None)

    if descarga_24h is None and isinstance(resultado_bateria, dict):
        descarga_24h = resultado_bateria.get("descarga_24h_kwh")

    if isinstance(descarga_24h, list):
        total = 0.0
        for x in descarga_24h:
            try:
                total += float(x or 0.0)
            except Exception:
                pass
        return total

    tabla_24h = getattr(resultado_bateria, "tabla_24h", None)

    if tabla_24h is None and isinstance(resultado_bateria, dict):
        tabla_24h = resultado_bateria.get("tabla_24h")

    if isinstance(tabla_24h, list):
        total = 0.0

        for fila in tabla_24h:
            if not isinstance(fila, dict):
                continue

            for campo in [
                "descarga_kwh",
                "energia_descargada_kwh",
                "energia_entregada_kwh",
                "bateria_a_carga_kwh",
            ]:
                if campo in fila:
                    try:
                        total += float(fila.get(campo) or 0.0)
                    except Exception:
                        pass
                    break

        return total

    return 0.0


def _energia_fv_12m_con_bateria(
    *,
    consumo_12m: List[float],
    energia_fv_12m: List[float],
    energia_generada_12m: List[float],
    resultado_bateria,
) -> List[float]:

    energia_fv_12m = _normalizar_energia(energia_fv_12m)

    if energia_generada_12m:
        energia_generada_12m = _normalizar_energia(energia_generada_12m)
    else:
        energia_generada_12m = energia_fv_12m[:]

    dias_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    energia_bateria_dia = _energia_descargada_bateria_diaria(resultado_bateria)

    resultado = []

    for i in range(12):
        consumo = float(consumo_12m[i])
        fv_util = float(energia_fv_12m[i])
        fv_generada = float(energia_generada_12m[i])

        excedente_mes = max(fv_generada - fv_util, 0.0)
        deficit_mes = max(consumo - fv_util, 0.0)
        bateria_mes = max(energia_bateria_dia, 0.0) * dias_mes[i]

        adicional = min(excedente_mes, deficit_mes, bateria_mes)

        resultado.append(min(consumo, fv_util + adicional))

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

    if deuda_mensual > 0:
        dscr = ahorro_prom / deuda_mensual
    else:
        dscr = None

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


def evaluar_opciones_bateria_financieras(
    *,
    datos: Datosproyecto,
    energia: EnergiaResultado,
    capex_fv_L: float,
    tarifa_energia: float,
    cargos_fijos: float,
    tasa_anual: float,
    plazo_anios: int,
    pct_fin: float,
    om_anual_pct: float,
) -> Dict[str, Any]:

    opciones = getattr(energia, "opciones_bateria", None) or []

    demanda_24h = getattr(datos, "consumo_horario_24h_kwh", {}) or {}
    fv_24h = getattr(energia, "energia_horaria_kwh", None)

    costo_bateria_usd_kwh = float(
        getattr(datos, "costo_bateria_usd_kwh", 250.0) or 250.0
    )

    tcambio = float(getattr(datos, "tcambio", 26.61) or 26.61)

    escenarios = []

    capex_base = float(capex_fv_L)

    cuota_base = calcular_cuota_mensual(
        capex_L_=capex_base,
        tasa_anual=tasa_anual,
        plazo_anios=plazo_anios,
        pct_fin=pct_fin,
    )

    om_base = om_mensual(capex_base, om_anual_pct)

    tabla_base = simular_12_meses(
        consumo_12m=datos.consumo_12m,
        energia_fv_12m=getattr(energia, "energia_util_12m", []),
        tarifa_energia=tarifa_energia,
        cargos_fijos=cargos_fijos,
        cuota_mensual=cuota_base,
        om_mensual_val=om_base,
    )

    ahorro_anual_base = sum(x["ahorro_L"] for x in tabla_base)
    evaluacion_base = _evaluacion_mensual(tabla_base, cuota_base)

    escenarios.append({
        "nombre": "Sin batería",
        "capacidad_bateria_kwh": 0.0,
        "potencia_bateria_kw": 0.0,
        "capex_bateria_L": 0.0,
        "capex_total_L": capex_base,
        "cuota_mensual_L": cuota_base,
        "om_mensual_L": om_base,
        "ahorro_anual_L": ahorro_anual_base,
        "payback_anios": capex_base / ahorro_anual_base if ahorro_anual_base > 0 else None,
        "roi_pct": (ahorro_anual_base / capex_base) * 100 if capex_base > 0 else 0.0,
        "evaluacion": evaluacion_base,
        "tabla_12m": tabla_base,
        "resultado_bateria": None,
    })

    if not demanda_24h or not fv_24h:
        return {
            "escenarios": escenarios,
            "mejor": escenarios[0],
        }

    energia_generada_12m = (
        getattr(energia, "energia_generada_12m", None)
        or getattr(energia, "energia_bruta_12m", None)
        or getattr(energia, "energia_fv_12m", None)
        or getattr(energia, "produccion_12m", None)
        or getattr(energia, "energia_util_12m", [])
    )

    for opcion in opciones:
        capacidad_kwh = float(
            getattr(opcion, "capacidad_util_kwh", 0.0) or 0.0
        )

        potencia_kw = float(
            getattr(opcion, "potencia_max_kw", 0.0) or 0.0
        )

        if capacidad_kwh <= 0 or potencia_kw <= 0:
            continue

        cfg = ConfigBateria(
            usar_bateria=True,
            capacidad_util_kwh=capacidad_kwh,
            potencia_max_kw=potencia_kw,
            soc_inicial_pct=20.0,
            soc_min_pct=20.0,
            soc_max_pct=100.0,
            eficiencia_ida_vuelta=0.90,
            costo_usd_kwh=costo_bateria_usd_kwh,
            vida_util_anios=10,
        )

        resultado_bateria = ejecutar_bateria(
            demanda_24h=demanda_24h,
            fv_24h=fv_24h,
            cfg_bateria=cfg,
        )

        if resultado_bateria is None or not getattr(resultado_bateria, "ok", False):
            continue

        capex_bateria = capacidad_kwh * costo_bateria_usd_kwh * tcambio
        capex_total = capex_fv_L + capex_bateria

        cuota = calcular_cuota_mensual(
            capex_L_=capex_total,
            tasa_anual=tasa_anual,
            plazo_anios=plazo_anios,
            pct_fin=pct_fin,
        )

        om_val = om_mensual(capex_total, om_anual_pct)

        energia_fv_12m_bateria = _energia_fv_12m_con_bateria(
            consumo_12m=datos.consumo_12m,
            energia_fv_12m=getattr(energia, "energia_util_12m", []),
            energia_generada_12m=energia_generada_12m,
            resultado_bateria=resultado_bateria,
        )

        tabla = simular_12_meses(
            consumo_12m=datos.consumo_12m,
            energia_fv_12m=energia_fv_12m_bateria,
            tarifa_energia=tarifa_energia,
            cargos_fijos=cargos_fijos,
            cuota_mensual=cuota,
            om_mensual_val=om_val,
        )

        ahorro_anual = sum(x["ahorro_L"] for x in tabla)
        evaluacion = _evaluacion_mensual(tabla, cuota)

        escenarios.append({
            "nombre": f"Batería {capacidad_kwh:.0f} kWh",
            "capacidad_bateria_kwh": capacidad_kwh,
            "potencia_bateria_kw": potencia_kw,
            "capex_bateria_L": capex_bateria,
            "capex_total_L": capex_total,
            "cuota_mensual_L": cuota,
            "om_mensual_L": om_val,
            "ahorro_anual_L": ahorro_anual,
            "payback_anios": capex_total / ahorro_anual if ahorro_anual > 0 else None,
            "roi_pct": (ahorro_anual / capex_total) * 100 if capex_total > 0 else 0.0,
            "evaluacion": evaluacion,
            "tabla_12m": tabla,
            "resultado_bateria": resultado_bateria,
            "energia_fv_12m_bateria": energia_fv_12m_bateria,
        })

    escenarios_validos = [
        e for e in escenarios
        if e.get("payback_anios") is not None
    ]

    if escenarios_validos:
        mejor = min(
            escenarios_validos,
            key=lambda e: e["payback_anios"]
        )
    else:
        mejor = escenarios[0]

    return {
        "escenarios": escenarios,
        "mejor": mejor,
    }


# ==========================================================
# 🔵 ENTRYPOINT FINANCIERO
# ==========================================================

def ejecutar_finanzas(
    *,
    datos: Datosproyecto,
    sizing: ResultadoSizing,
    energia: EnergiaResultado,
    bateria=None,
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

    capex_fv = calcular_capex_L(
        pdc_kw=kwp_dc,
        costo_usd_kwp=datos.costo_usd_kwp,
        tcambio=datos.tcambio,
    )

    capex_bateria = 0.0
    capacidad_bateria_kwh = 0.0
    costo_bateria_usd_kwh = 0.0

    if bateria is not None and getattr(bateria, "ok", False):

        capacidad_bateria_kwh = float(
            getattr(bateria, "capacidad_util_kwh", 0.0) or 0.0
        )

        costo_bateria_usd_kwh = float(
            getattr(bateria, "costo_usd_kwh", 0.0) or 0.0
        )

        if capacidad_bateria_kwh <= 0:
            bateria_rec = getattr(energia, "bateria_recomendada", None)

            if bateria_rec is not None:
                capacidad_bateria_kwh = float(
                    getattr(
                        bateria_rec,
                        "capacidad_util_kwh",
                        0.0
                    ) or 0.0
                )

        capex_bateria = (
            capacidad_bateria_kwh
            * costo_bateria_usd_kwh
            * float(datos.tcambio)
        )

    capex = capex_fv + capex_bateria

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

    roi = (ahorro_anual / capex) * 100 if capex > 0 else 0.0
    payback = capex / ahorro_anual if ahorro_anual > 0 else 0.0

    flujos = [-capex]

    for _ in range(10):
        flujos.append(ahorro_anual)

    tir = _tir(flujos) * 100

    optimizacion_bateria = evaluar_opciones_bateria_financieras(
        datos=datos,
        energia=energia,
        capex_fv_L=capex_fv,
        tarifa_energia=datos.tarifa_energia,
        cargos_fijos=datos.cargos_fijos,
        tasa_anual=datos.tasa_anual,
        plazo_anios=datos.plazo_anios,
        pct_fin=datos.porcentaje_financiado,
        om_anual_pct=datos.om_anual_pct,
    )

    return {
        "capex_L": capex,
        "capex_fv_L": capex_fv,
        "capex_bateria_L": capex_bateria,
        "capacidad_bateria_kwh": capacidad_bateria_kwh,
        "costo_bateria_usd_kwh": costo_bateria_usd_kwh,
        "cuota_mensual": cuota,
        "tabla_12m": tabla_12m,
        "evaluacion": evaluacion,
        "ahorro_anual_L": ahorro_anual,
        "roi_pct": roi,
        "payback_anios": payback,
        "tir_pct": tir,
        "optimizacion_bateria": optimizacion_bateria,
        "escenarios_bateria": optimizacion_bateria["escenarios"],
        "bateria_optima": optimizacion_bateria["mejor"],
    }
