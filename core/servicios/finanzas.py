from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.dominio.modelo import Datosproyecto
from core.dominio.contrato import ResultadoSizing
from energy.resultado_energia import EnergiaResultado
from energy.baterias.modelos import ConfigBateria
from energy.baterias.orquestador_bateria import ejecutar_bateria


# ==========================================================
# 🔵 PERFIL FINANCIERO POR DEFECTO
# ==========================================================

PERFIL_FINANCIAMIENTO_DEFAULT = {
    "nombre": "Crédito PyME Invierta Prendario",
    "entidad": "Banco",
    "tasa_anual": 0.195,
    "cat": 0.2196,
    "plazo_anios": 7,
    "plazo_meses": 84,
    "prima_pct": 0.10,
    "porcentaje_financiado": 0.90,
    "nota": (
        "Condiciones referenciales sujetas a evaluación crediticia, "
        "garantías, comisiones, seguros y aprobación final de la entidad financiera."
    ),
}


def obtener_perfil_financiamiento(
    datos: Datosproyecto | None = None,
) -> Dict[str, Any]:
    """
    Construye el perfil financiero del proyecto.

    Reglas:
    - contado: prima 100%, financiamiento 0%.
    - credito_100: prima 0%, financiamiento 100%.
    - credito_con_prima:
        porcentaje_financiado = 1 - prima_pct.

    La prima es la fuente principal para evitar inconsistencias
    entre prima_pct y porcentaje_financiado.
    """

    perfil = dict(PERFIL_FINANCIAMIENTO_DEFAULT)

    if datos is None:
        perfil["modo_financiamiento"] = "credito_con_prima"
        return perfil

    modo = str(
        getattr(
            datos,
            "modo_financiamiento",
            "credito_con_prima",
        )
        or "credito_con_prima"
    ).strip().lower()

    nombre = getattr(datos, "nombre_financiamiento", None)
    entidad = getattr(datos, "entidad_financiera", None)
    tasa = getattr(datos, "tasa_anual", None)
    plazo_anios = getattr(datos, "plazo_anios", None)
    prima_datos = getattr(datos, "prima_pct", None)
    pct_fin_datos = getattr(datos, "porcentaje_financiado", None)
    cat = getattr(datos, "cat", None)

    if nombre:
        perfil["nombre"] = str(nombre)

    if entidad:
        perfil["entidad"] = str(entidad)

    try:
        if tasa is not None:
            perfil["tasa_anual"] = float(tasa)
    except (TypeError, ValueError):
        pass

    try:
        if plazo_anios is not None:
            perfil["plazo_anios"] = int(plazo_anios)
            perfil["plazo_meses"] = int(plazo_anios) * 12
    except (TypeError, ValueError):
        pass

    try:
        if cat is not None:
            perfil["cat"] = float(cat)
    except (TypeError, ValueError):
        pass

    # ======================================================
    # MODO: CONTADO
    # ======================================================
    if modo == "contado":
        perfil["modo_financiamiento"] = "contado"
        perfil["nombre"] = "Pago de contado"
        perfil["entidad"] = "Cliente"
        perfil["tasa_anual"] = 0.0
        perfil["cat"] = 0.0
        perfil["plazo_anios"] = 0
        perfil["plazo_meses"] = 0
        perfil["prima_pct"] = 1.0
        perfil["porcentaje_financiado"] = 0.0
        perfil["nota"] = (
            "Proyecto evaluado bajo esquema de pago de contado, "
            "sin deuda financiera."
        )

        return perfil

    # ======================================================
    # MODO: CRÉDITO 100%
    # ======================================================
    if modo in [
        "credito_100",
        "credito100",
        "financiado_100",
    ]:
        perfil["modo_financiamiento"] = "credito_100"
        perfil["nombre"] = "Crédito 100% financiado"
        perfil["prima_pct"] = 0.0
        perfil["porcentaje_financiado"] = 1.0

        return perfil

    # ======================================================
    # MODO: CRÉDITO CON PRIMA
    # ======================================================
    perfil["modo_financiamiento"] = "credito_con_prima"

    # La prima tiene prioridad porque es el valor capturado
    # directamente en la interfaz.
    if prima_datos is not None:
        try:
            prima_pct = float(prima_datos)
        except (TypeError, ValueError):
            prima_pct = 0.10

        prima_pct = max(0.0, min(1.0, prima_pct))
        pct_fin = 1.0 - prima_pct

    elif pct_fin_datos is not None:
        try:
            pct_fin = float(pct_fin_datos)
        except (TypeError, ValueError):
            pct_fin = 0.90

        pct_fin = max(0.0, min(1.0, pct_fin))
        prima_pct = 1.0 - pct_fin

    else:
        prima_pct = 0.10
        pct_fin = 0.90

    perfil["prima_pct"] = prima_pct
    perfil["porcentaje_financiado"] = pct_fin

    # Una prima del 100% equivale financieramente
    # a una compra de contado.
    if prima_pct >= 1.0:
        perfil["modo_financiamiento"] = "contado"
        perfil["nombre"] = "Pago de contado"
        perfil["entidad"] = "Cliente"
        perfil["tasa_anual"] = 0.0
        perfil["cat"] = 0.0
        perfil["plazo_anios"] = 0
        perfil["plazo_meses"] = 0
        perfil["prima_pct"] = 1.0
        perfil["porcentaje_financiado"] = 0.0
        perfil["nota"] = (
            "Proyecto evaluado bajo modalidad de pago de contado, "
            "sin deuda financiera."
        )

    return perfil

def calcular_detalle_financiamiento(
    *,
    capex_L_: float,
    perfil: Dict[str, Any],
) -> Dict[str, float]:
    """
    Calcula prima y monto financiado manteniendo consistencia.

    No utiliza `or` porque 0.0 es un valor financiero válido.
    """

    capex = float(capex_L_ or 0.0)

    prima_valor = perfil.get("prima_pct", 0.0)

    if prima_valor is None:
        prima_valor = 0.0

    prima_pct = max(
        0.0,
        min(1.0, float(prima_valor)),
    )

    # La prima determina el porcentaje financiado.
    porcentaje_financiado = 1.0 - prima_pct

    prima_L = capex * prima_pct
    monto_financiado_L = capex * porcentaje_financiado

    return {
        "prima_pct": prima_pct,
        "prima_L": prima_L,
        "porcentaje_financiado": porcentaje_financiado,
        "monto_financiado_L": monto_financiado_L,
    }

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


def _energia_descargada_bateria_diaria(
    resultado_bateria,
) -> float:

    if resultado_bateria is None:
        return 0.0

    # Primero intenta leer el total diario ya calculado
    # por el simulador de batería.
    valor_directo = _extraer_valor_bateria(
        resultado_bateria,
        [
            "energia_descargada_bateria_kwh",
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

    # Fallback: sumar la serie horaria.
    descarga_24h = getattr(
        resultado_bateria,
        "descarga_bateria_24h",
        None,
    )

    if descarga_24h is None:
        descarga_24h = getattr(
            resultado_bateria,
            "descarga_24h_kwh",
            None,
        )

    if isinstance(resultado_bateria, dict):

        if descarga_24h is None:
            descarga_24h = resultado_bateria.get(
                "descarga_bateria_24h"
            )

        if descarga_24h is None:
            descarga_24h = resultado_bateria.get(
                "descarga_24h_kwh"
            )

    if isinstance(descarga_24h, (list, tuple)):
        return sum(
            float(x or 0.0)
            for x in descarga_24h
        )

    # Último fallback para formatos antiguos.
    tabla_24h = getattr(
        resultado_bateria,
        "tabla_24h",
        None,
    )

    if tabla_24h is None and isinstance(
        resultado_bateria,
        dict,
    ):
        tabla_24h = resultado_bateria.get("tabla_24h")

    if isinstance(tabla_24h, list):

        total = 0.0

        for fila in tabla_24h:

            if not isinstance(fila, dict):
                continue

            for campo in [
                "descarga_bateria_kwh",
                "descarga_kwh",
                "energia_descargada_kwh",
                "energia_entregada_kwh",
                "bateria_a_carga_kwh",
            ]:
                if campo in fila:
                    total += float(
                        fila.get(campo) or 0.0
                    )
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


def calcular_cuota_mensual_perfil(
    *,
    capex_L_: float,
    perfil: Dict[str, Any],
) -> float:
    """
    Calcula cuota mensual según perfil financiero.

    Si es contado o no hay monto financiado, la cuota es 0.
    """

    modo = str(perfil.get("modo_financiamiento", "") or "").strip().lower()
    pct_fin = float(perfil.get("porcentaje_financiado", 1.0) or 0.0)
    plazo_anios = int(perfil.get("plazo_anios", 0) or 0)

    if modo == "contado":
        return 0.0

    if pct_fin <= 0:
        return 0.0

    if plazo_anios <= 0:
        return 0.0

    return calcular_cuota_mensual(
        capex_L_=capex_L_,
        tasa_anual=float(perfil.get("tasa_anual", 0.0) or 0.0),
        plazo_anios=plazo_anios,
        pct_fin=pct_fin,
    )

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
    """
    Evalúa el comportamiento financiero mensual.

    Reglas:
    - El DSCR solo se calcula cuando existe deuda financiera.
    - El O&M es un gasto operativo, no servicio de deuda.
    - En pago de contado, DSCR = None.
    """

    if not tabla:
        return {
            "estado": "ERROR",
            "nota": "Tabla financiera vacía",
            "dscr": None,
            "ahorro_prom": 0.0,
            "neto_prom": 0.0,
            "peor_mes": 0.0,
        }

    ahorros = [
        float(x.get("ahorro_L", 0.0) or 0.0)
        for x in tabla
    ]

    netos = [
        float(x.get("neto_L", 0.0) or 0.0)
        for x in tabla
    ]

    ahorro_prom = sum(ahorros) / len(ahorros)
    neto_prom = sum(netos) / len(netos)
    peor_mes = min(netos)

    cuota_mensual = max(
        0.0,
        float(cuota or 0.0),
    )

    # ======================================================
    # PAGO DE CONTADO — SIN SERVICIO DE DEUDA
    # ======================================================

    if cuota_mensual <= 0:
        dscr = None

        if neto_prom > 0 and peor_mes >= 0:
            estado = "VIABLE"
            nota = (
                "Proyecto evaluado sin deuda financiera. "
                "El flujo neto es positivo en todos los meses."
            )

        elif neto_prom > 0:
            estado = "VIABLE CON OBSERVACIONES"
            nota = (
                "Proyecto evaluado sin deuda financiera. "
                "El flujo promedio es positivo, aunque existen "
                "meses que requieren revisión."
            )

        else:
            estado = "NO VIABLE"
            nota = (
                "Proyecto evaluado sin deuda financiera, pero los "
                "ahorros no cubren adecuadamente los costos operativos."
            )

    # ======================================================
    # PROYECTO FINANCIADO — EVALUAR DSCR
    # ======================================================

    else:
        # El DSCR mide cobertura del servicio de deuda.
        # El O&M ya está incluido en el flujo neto y no debe
        # sumarse nuevamente al denominador.
        dscr = ahorro_prom / cuota_mensual

        if dscr >= 1.20 and neto_prom > 0 and peor_mes >= 0:
            estado = "VIABLE"
            nota = (
                "Excelente cobertura financiera. "
                "Flujo positivo en todos los meses."
            )

        elif dscr >= 1.00 and neto_prom > 0:
            estado = "ACEPTABLE"
            nota = (
                "El proyecto cubre el servicio de deuda, aunque "
                "su margen financiero debe revisarse."
            )

        elif dscr >= 0.80:
            estado = "MARGINAL"
            nota = (
                "Cobertura financiera ajustada. "
                "Algunos meses pueden presentar flujo insuficiente."
            )

        else:
            estado = "NO VIABLE"
            nota = (
                "Los ahorros no cubren adecuadamente "
                "el servicio de deuda."
            )

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
# 🔵 Optimización financiera de baterías
# ==========================================================

def _resumen_escenario_financiero(
    *,
    evaluacion: dict,
    capex_total: float,
    ahorro_anual: float,
) -> dict:
    """
    Campos planos para facilitar PDF / tablas / selección.
    No reemplaza la evaluación original; solo la expone más fácil.
    """

    ahorro_neto_mensual = float(evaluacion.get("neto_prom", 0.0) or 0.0)
    dscr = evaluacion.get("dscr", None)
    peor_mes = float(evaluacion.get("peor_mes", 0.0) or 0.0)
    estado = evaluacion.get("estado", "SIN ESTADO")

    return {
        "ahorro_neto_mensual_L": ahorro_neto_mensual,
        "dscr": dscr,
        "peor_mes_L": peor_mes,
        "estado": estado,
        "payback_anios": capex_total / ahorro_anual if ahorro_anual > 0 else None,
        "roi_pct": (ahorro_anual / capex_total) * 100 if capex_total > 0 else 0.0,
    }


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
    perfil_financiamiento: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    perfil = perfil_financiamiento or {
        "nombre": "Personalizado",
        "tasa_anual": tasa_anual,
        "plazo_anios": plazo_anios,
        "plazo_meses": int(plazo_anios) * 12,
        "porcentaje_financiado": pct_fin,
        "prima_pct": max(0.0, 1.0 - float(pct_fin)),
        "cat": None,
        "nota": "",
    }

    opciones = getattr(energia, "opciones_bateria", None) or []

    demanda_24h = getattr(datos, "consumo_horario_24h_kwh", {}) or {}
    fv_24h = getattr(energia, "energia_horaria_kwh", None)

    costo_bateria_usd_kwh = float(
        getattr(datos, "costo_bateria_usd_kwh", 250.0) or 250.0
    )

    tcambio = float(getattr(datos, "tcambio", 26.61) or 26.61)

    escenarios = []

    capex_base = float(capex_fv_L)

    cuota_base = calcular_cuota_mensual_perfil(
        capex_L_=capex_base,
        perfil=perfil,
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

    resumen_base = _resumen_escenario_financiero(
        evaluacion=evaluacion_base,
        capex_total=capex_base,
        ahorro_anual=ahorro_anual_base,
    )

    detalle_base = calcular_detalle_financiamiento(
        capex_L_=capex_base,
        perfil=perfil,
    )

    escenario_base = {
        "nombre": "Sin batería",
        "capacidad_bateria_kwh": 0.0,
        "potencia_bateria_kw": 0.0,
        "capex_bateria_L": 0.0,
        "capex_total_L": capex_base,
        "cuota_mensual_L": cuota_base,
        "om_mensual_L": om_base,
        "ahorro_anual_L": ahorro_anual_base,
        "evaluacion": evaluacion_base,
        "tabla_12m": tabla_base,
        "resultado_bateria": None,

        # Nuevos campos financieros, no rompen salida anterior
        "financiamiento": perfil,
        "nombre_financiamiento": perfil.get("nombre"),
        "entidad_financiera": perfil.get("entidad"),
        "tasa_anual": perfil.get("tasa_anual"),
        "cat": perfil.get("cat"),
        "plazo_anios": perfil.get("plazo_anios"),
        "plazo_meses": perfil.get("plazo_meses"),
        "prima_pct": detalle_base["prima_pct"],
        "prima_L": detalle_base["prima_L"],
        "porcentaje_financiado": detalle_base["porcentaje_financiado"],
        "monto_financiado_L": detalle_base["monto_financiado_L"],
    }

    escenario_base.update(resumen_base)
    escenarios.append(escenario_base)

    if not demanda_24h or not fv_24h:
        return {
            "escenarios": escenarios,
            "mejor": escenarios[0],
        }

    bateria_recomendada = getattr(energia, "bateria_recomendada", None)

    energia_objetivo_kwh = float(
        getattr(bateria_recomendada, "energia_objetivo_kwh", 0.0) or 0.0
    )

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

        energia_descargada_dia = _energia_descargada_bateria_diaria(
            resultado_bateria
        )

        capex_bateria = capacidad_kwh * costo_bateria_usd_kwh * tcambio
        capex_total = capex_fv_L + capex_bateria

        cuota = calcular_cuota_mensual_perfil(
            capex_L_=capex_total,
            perfil=perfil,
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

        resumen = _resumen_escenario_financiero(
            evaluacion=evaluacion,
            capex_total=capex_total,
            ahorro_anual=ahorro_anual,
        )

        detalle = calcular_detalle_financiamiento(
            capex_L_=capex_total,
            perfil=perfil,
        )

        escenario = {
            "nombre": f"Batería {capacidad_kwh:.0f} kWh",
            "capacidad_bateria_kwh": capacidad_kwh,
            "potencia_bateria_kw": potencia_kw,
            "capex_bateria_L": capex_bateria,
            "capex_total_L": capex_total,
            "cuota_mensual_L": cuota,
            "om_mensual_L": om_val,
            "ahorro_anual_L": ahorro_anual,
            "evaluacion": evaluacion,
            "tabla_12m": tabla,
            "resultado_bateria": resultado_bateria,
            "energia_fv_12m_bateria": energia_fv_12m_bateria,
            "energia_descargada_dia_kwh": energia_descargada_dia,
            "energia_objetivo_kwh": energia_objetivo_kwh,

            # Nuevos campos financieros
            "financiamiento": perfil,
            "nombre_financiamiento": perfil.get("nombre"),
            "entidad_financiera": perfil.get("entidad"),
            "tasa_anual": perfil.get("tasa_anual"),
            "cat": perfil.get("cat"),
            "plazo_anios": perfil.get("plazo_anios"),
            "plazo_meses": perfil.get("plazo_meses"),
            "prima_pct": detalle["prima_pct"],
            "prima_L": detalle["prima_L"],
            "porcentaje_financiado": detalle["porcentaje_financiado"],
            "monto_financiado_L": detalle["monto_financiado_L"],
        }

        escenario.update(resumen)
        escenarios.append(escenario)

    escenarios_validos = [
        e for e in escenarios
        if e.get("evaluacion") is not None
    ]

    escenarios_con_bateria = [
        e for e in escenarios_validos
        if float(e.get("capacidad_bateria_kwh", 0.0) or 0.0) > 0
    ]

    if escenarios_con_bateria and energia_objetivo_kwh > 0:

        escenarios_que_cumplen = [
            e for e in escenarios_con_bateria
            if float(e.get("energia_descargada_dia_kwh", 0.0) or 0.0)
            >= energia_objetivo_kwh * 0.95
        ]

        if escenarios_que_cumplen:
            mejor = min(
                escenarios_que_cumplen,
                key=lambda e: (
                    float(e.get("capacidad_bateria_kwh", 999999) or 999999),
                    float(e.get("capex_total_L", 999999999) or 999999999),
                )
            )
        else:
            mejor = min(
                escenarios_con_bateria,
                key=lambda e: (
                    abs(
                        float(e.get("energia_descargada_dia_kwh", 0.0) or 0.0)
                        - energia_objetivo_kwh
                    ),
                    float(e.get("capex_total_L", 999999999) or 999999999),
                )
            )

    elif escenarios_con_bateria:
        mejor = max(
            escenarios_con_bateria,
            key=lambda e: (
                float(e.get("energia_descargada_dia_kwh", 0.0) or 0.0),
                float(e.get("ahorro_neto_mensual_L", -999999) or -999999),
                -float(e.get("capex_total_L", 0.0) or 0.0),
            )
        )

    else:
        mejor = escenarios[0]

    return {
        "escenarios": escenarios,
        "mejor": mejor,
    }

def ejecutar_finanzas(
    *,
    datos: Datosproyecto,
    sizing: ResultadoSizing,
    energia: EnergiaResultado,
    bateria=None,
) -> Dict[str, Any]:

    kwp_dc = float(sizing.pdc_kw)

    if kwp_dc <= 0:
        raise ValueError(
            "Sizing incompleto para finanzas."
        )

    if energia is None:
        raise ValueError(
            "Resultado energético no definido."
        )

    if not energia.ok:
        raise ValueError(
            f"Energía inválida: {energia.errores}"
        )

    energia_fv_12m = getattr(
        energia,
        "energia_util_12m",
        None,
    )

    if (
        not energia_fv_12m
        or len(energia_fv_12m) != 12
    ):
        raise ValueError(
            "Energía mensual inválida."
        )

    # ======================================================
    # DATOS FINANCIEROS BASE
    # ======================================================

    perfil_financiamiento = (
        obtener_perfil_financiamiento(datos)
    )

    capex_fv = calcular_capex_L(
        pdc_kw=kwp_dc,
        costo_usd_kwp=datos.costo_usd_kwp,
        tcambio=datos.tcambio,
    )

    # ======================================================
    # EVALUAR ESCENARIOS DE BATERÍA
    # ======================================================

    optimizacion_bateria = (
        evaluar_opciones_bateria_financieras(
            datos=datos,
            energia=energia,
            capex_fv_L=capex_fv,
            tarifa_energia=datos.tarifa_energia,
            cargos_fijos=datos.cargos_fijos,
            tasa_anual=float(
                perfil_financiamiento.get(
                    "tasa_anual",
                    0.0,
                ) or 0.0
            ),
            plazo_anios=int(
                perfil_financiamiento.get(
                    "plazo_anios",
                    0,
                ) or 0
            ),
            pct_fin=float(
                perfil_financiamiento.get(
                    "porcentaje_financiado",
                    1.0,
                ) or 1.0
            ),
            om_anual_pct=datos.om_anual_pct,
            perfil_financiamiento=(
                perfil_financiamiento
            ),
        )
    )

    escenarios = (
        optimizacion_bateria.get(
            "escenarios",
            [],
        )
        or []
    )

    mejor = (
        optimizacion_bateria.get("mejor")
        or (
            escenarios[0]
            if escenarios
            else None
        )
    )

    if not isinstance(mejor, dict):
        raise ValueError(
            "No se obtuvo un escenario financiero válido."
        )

    # ======================================================
    # CONSOLIDAR ESCENARIO SELECCIONADO
    # ======================================================

    capex = float(
        mejor.get(
            "capex_total_L",
            capex_fv,
        ) or capex_fv
    )

    capex_bateria = float(
        mejor.get(
            "capex_bateria_L",
            0.0,
        ) or 0.0
    )

    capacidad_bateria_kwh = float(
        mejor.get(
            "capacidad_bateria_kwh",
            0.0,
        ) or 0.0
    )

    potencia_bateria_kw = float(
        mejor.get(
            "potencia_bateria_kw",
            0.0,
        ) or 0.0
    )

    costo_bateria_usd_kwh = (
        float(
            getattr(
                datos,
                "costo_bateria_usd_kwh",
                250.0,
            ) or 250.0
        )
        if capacidad_bateria_kwh > 0
        else 0.0
    )

    cuota = float(
        mejor.get(
            "cuota_mensual_L",
            0.0,
        ) or 0.0
    )

    tabla_12m = (
        mejor.get("tabla_12m")
        or []
    )

    evaluacion = (
        mejor.get("evaluacion")
        or {}
    )

    ahorro_anual = float(
        mejor.get(
            "ahorro_anual_L",
            0.0,
        ) or 0.0
    )

    roi = (
        ahorro_anual / capex * 100.0
        if capex > 0
        else 0.0
    )

    payback = (
        capex / ahorro_anual
        if ahorro_anual > 0
        else 0.0
    )

    flujos = [-capex]

    for _ in range(10):
        flujos.append(ahorro_anual)

    tir = _tir(flujos) * 100.0

    # ======================================================
    # FINANCIAMIENTO DEL ESCENARIO SELECCIONADO
    # ======================================================

    detalle_financiamiento = (
        calcular_detalle_financiamiento(
            capex_L_=capex,
            perfil=perfil_financiamiento,
        )
    )

    # ======================================================
    # RESULTADO FINANCIERO CONSOLIDADO
    # ======================================================

    return {
        "capex_L": capex,
        "capex_total_L": capex,
        "capex_fv_L": capex_fv,
        "capex_bateria_L": capex_bateria,

        "capacidad_bateria_kwh": (
            capacidad_bateria_kwh
        ),
        "potencia_bateria_kw": (
            potencia_bateria_kw
        ),
        "costo_bateria_usd_kwh": (
            costo_bateria_usd_kwh
        ),

        "cuota_mensual": cuota,
        "cuota_mensual_L": cuota,

        "tabla_12m": tabla_12m,
        "evaluacion": evaluacion,
        "ahorro_anual_L": ahorro_anual,
        "roi_pct": roi,
        "payback_anios": payback,
        "tir_pct": tir,

        "optimizacion_bateria": (
            optimizacion_bateria
        ),
        "escenarios_bateria": escenarios,
        "bateria_optima": mejor,

        "financiamiento": perfil_financiamiento,
        "modo_financiamiento": (
            perfil_financiamiento.get(
                "modo_financiamiento"
            )
        ),
        "nombre_financiamiento": (
            perfil_financiamiento.get("nombre")
        ),
        "entidad_financiera": (
            perfil_financiamiento.get("entidad")
        ),
        "nota_financiamiento": (
            perfil_financiamiento.get("nota")
        ),
        "tasa_anual": (
            perfil_financiamiento.get(
                "tasa_anual"
            )
        ),
        "cat": perfil_financiamiento.get("cat"),
        "plazo_anios": (
            perfil_financiamiento.get(
                "plazo_anios"
            )
        ),
        "plazo_meses": (
            perfil_financiamiento.get(
                "plazo_meses"
            )
        ),

        "prima_pct": (
            detalle_financiamiento["prima_pct"]
        ),
        "prima_L": (
            detalle_financiamiento["prima_L"]
        ),
        "porcentaje_financiado": (
            detalle_financiamiento[
                "porcentaje_financiado"
            ]
        ),
        "monto_financiado_L": (
            detalle_financiamiento[
                "monto_financiado_L"
            ]
        ),
    }
