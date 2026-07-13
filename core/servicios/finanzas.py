from __future__ import annotations

from typing import Any, Dict, List

from core.dominio.contrato import ResultadoSizing
from core.dominio.modelo import Datosproyecto
from energy.resultado_energia import EnergiaResultado


PERFIL_FINANCIAMIENTO_DEFAULT = {
    "nombre": "Crédito PyME Invierta Prendario",
    "entidad": "Banco",
    "tasa_anual": 0.195,
    "cat": 0.2196,
    "plazo_anios": 7,
    "plazo_meses": 84,
    "prima_pct": 0.10,
    "porcentaje_financiado": 0.90,
    "nota": "Condiciones referenciales sujetas a aprobación financiera.",
}


def _float(valor, default=0.0) -> float:
    try:
        return float(valor if valor is not None else default)
    except (TypeError, ValueError):
        return float(default)


def _int(valor, default=0) -> int:
    try:
        return int(valor if valor is not None else default)
    except (TypeError, ValueError):
        return int(default)


def _limitar(valor, minimo=0.0, maximo=1.0) -> float:
    return max(minimo, min(maximo, _float(valor)))


def _leer(objeto, campo, default=None):
    if objeto is None:
        return default
    if isinstance(objeto, dict):
        return objeto.get(campo, default)
    return getattr(objeto, campo, default)


# ==========================================================
# PERFIL DE FINANCIAMIENTO
# ==========================================================

def _perfil_contado() -> Dict[str, Any]:
    return {
        "modo_financiamiento": "contado",
        "nombre": "Pago de contado",
        "entidad": "Cliente",
        "tasa_anual": 0.0,
        "cat": 0.0,
        "plazo_anios": 0,
        "plazo_meses": 0,
        "prima_pct": 1.0,
        "porcentaje_financiado": 0.0,
        "nota": "Proyecto evaluado sin deuda financiera.",
    }


def _actualizar_datos_perfil(perfil, datos) -> None:
    campos = {
        "nombre": "nombre_financiamiento",
        "entidad": "entidad_financiera",
        "tasa_anual": "tasa_anual",
        "cat": "cat",
    }
    for destino, origen in campos.items():
        valor = getattr(datos, origen, None)
        if valor is not None:
            perfil[destino] = valor

    plazo = _int(getattr(datos, "plazo_anios", perfil["plazo_anios"]))
    perfil["plazo_anios"] = plazo
    perfil["plazo_meses"] = plazo * 12


def _porcentajes_financiamiento(datos) -> tuple[float, float]:
    prima = getattr(datos, "prima_pct", None)
    financiado = getattr(datos, "porcentaje_financiado", None)

    if prima is not None:
        prima = _limitar(prima)
        return prima, 1.0 - prima

    financiado = _limitar(0.90 if financiado is None else financiado)
    return 1.0 - financiado, financiado


def obtener_perfil_financiamiento(
    datos: Datosproyecto | None = None,
) -> Dict[str, Any]:
    perfil = dict(PERFIL_FINANCIAMIENTO_DEFAULT)

    if datos is None:
        perfil["modo_financiamiento"] = "credito_con_prima"
        return perfil

    modo = str(
        getattr(datos, "modo_financiamiento", "credito_con_prima")
        or "credito_con_prima"
    ).strip().lower()

    if modo == "contado":
        return _perfil_contado()

    _actualizar_datos_perfil(perfil, datos)

    return _resolver_perfil_credito(
        perfil,
        datos,
        modo,
    )


def _resolver_perfil_credito(perfil, datos, modo):

    if modo in {"credito_100", "credito100", "financiado_100"}:
        perfil.update({
            "modo_financiamiento": "credito_100",
            "nombre": "Crédito 100% financiado",
            "prima_pct": 0.0,
            "porcentaje_financiado": 1.0,
        })
        return perfil

    prima, financiado = _porcentajes_financiamiento(datos)
    if prima >= 1.0:
        return _perfil_contado()

    perfil.update({
        "modo_financiamiento": "credito_con_prima",
        "prima_pct": prima,
        "porcentaje_financiado": financiado,
    })
    return perfil


def calcular_detalle_financiamiento(
    *,
    capex_L_: float,
    perfil: Dict[str, Any],
) -> Dict[str, float]:
    capex = max(0.0, _float(capex_L_))
    prima_pct = _limitar(perfil.get("prima_pct", 0.0))
    porcentaje = 1.0 - prima_pct

    return {
        "prima_pct": prima_pct,
        "prima_L": capex * prima_pct,
        "porcentaje_financiado": porcentaje,
        "monto_financiado_L": capex * porcentaje,
    }


# ==========================================================
# CÁLCULOS FINANCIEROS
# ==========================================================

def calcular_capex_L(pdc_kw, costo_usd_kwp, tcambio) -> float:
    return _float(pdc_kw) * _float(costo_usd_kwp) * _float(tcambio)


def calcular_cuota_mensual(capex_L_, tasa_anual, plazo_anios, pct_fin) -> float:
    principal = _float(capex_L_) * _limitar(pct_fin)
    meses = _int(plazo_anios) * 12

    if principal <= 0 or meses <= 0:
        return 0.0

    tasa = max(0.0, _float(tasa_anual)) / 12.0
    if tasa == 0:
        return principal / meses

    return tasa * principal / (1.0 - (1.0 + tasa) ** (-meses))


def calcular_cuota_mensual_perfil(*, capex_L_, perfil) -> float:
    if perfil.get("modo_financiamiento") == "contado":
        return 0.0

    return calcular_cuota_mensual(
        capex_L_,
        perfil.get("tasa_anual", 0.0),
        perfil.get("plazo_anios", 0),
        perfil.get("porcentaje_financiado", 0.0),
    )


def om_mensual(capex_L_: float, om_anual_pct: float) -> float:
    return _float(capex_L_) * _float(om_anual_pct) / 12.0


def _normalizar_12m(valores, nombre) -> List[float]:
    if not valores or len(valores) != 12:
        raise ValueError(f"{nombre} debe contener 12 valores.")
    return [max(0.0, _float(valor)) for valor in valores]


def simular_12_meses(
    *,
    consumo_12m,
    energia_fv_12m,
    tarifa_energia,
    cargos_fijos,
    cuota_mensual,
    om_mensual_val,
    compra_red_12m=None,
    inyeccion_12m=None,
    tarifa_inyeccion=0.0,
) -> List[Dict[str, float]]:
    consumo = _normalizar_12m(consumo_12m, "consumo_12m")
    energia = _normalizar_12m(energia_fv_12m, "energia_fv_12m")
    compra = (
        _normalizar_12m(compra_red_12m, "compra_red_12m")
        if compra_red_12m
        else [
            max(consumo[i] - min(consumo[i], energia[i]), 0.0)
            for i in range(12)
        ]
    )
    inyeccion = (
        _normalizar_12m(inyeccion_12m, "inyeccion_12m")
        if inyeccion_12m
        else [0.0] * 12
    )

    tabla = []
    saldo_credito = 0.0

    for i in range(12):
        fila = _fila_mensual(
            mes=i + 1,
            consumo=consumo[i],
            energia=energia[i],
            compra=compra[i],
            inyeccion=inyeccion[i],
            tarifa=_float(tarifa_energia),
            tarifa_inyeccion=_float(tarifa_inyeccion),
            cargos=_float(cargos_fijos),
            cuota=_float(cuota_mensual),
            om=_float(om_mensual_val),
            saldo_credito=saldo_credito,
        )
        saldo_credito = fila["saldo_credito_L"]
        tabla.append(fila)

    return tabla


def _fila_mensual(
    *,
    mes,
    consumo,
    energia,
    compra,
    inyeccion,
    tarifa,
    tarifa_inyeccion,
    cargos,
    cuota,
    om,
    saldo_credito,
) -> dict:
    fv_util = min(consumo, energia)
    kwh_enee = max(compra, 0.0)
    factura_base = consumo * tarifa + cargos
    cargo_energia = kwh_enee * tarifa
    credito_generado = max(inyeccion, 0.0) * tarifa_inyeccion
    credito_disponible = saldo_credito + credito_generado
    credito_aplicado = min(cargo_energia, credito_disponible)
    saldo_credito_final = credito_disponible - credito_aplicado
    pago_enee = cargo_energia - credito_aplicado + cargos
    ahorro = factura_base - pago_enee

    return {
        "mes": mes,
        "consumo_kwh": consumo,
        "fv_kwh": fv_util,
        "kwh_enee": kwh_enee,
        "inyeccion_kwh": max(inyeccion, 0.0),
        "factura_base_L": factura_base,
        "cargo_energia_enee_L": cargo_energia,
        "credito_inyeccion_generado_L": credito_generado,
        "credito_inyeccion_aplicado_L": credito_aplicado,
        "saldo_credito_L": saldo_credito_final,
        "pago_enee_L": pago_enee,
        "ahorro_L": ahorro,
        "cuota_L": cuota,
        "om_L": om,
        "neto_L": ahorro - cuota - om,
    }


def _evaluacion_mensual(tabla, cuota) -> dict:
    if not tabla:
        return _evaluacion_vacia()

    ahorro = sum(fila["ahorro_L"] for fila in tabla) / len(tabla)
    neto = sum(fila["neto_L"] for fila in tabla) / len(tabla)
    peor = min(fila["neto_L"] for fila in tabla)
    flujo_disponible = ahorro - sum(
        fila["om_L"] for fila in tabla
    ) / len(tabla)
    dscr = flujo_disponible / cuota if cuota > 0 else None
    estado, nota = _clasificar_evaluacion(dscr, neto, peor)

    return {
        "estado": estado,
        "nota": nota,
        "dscr": dscr,
        "ahorro_prom": ahorro,
        "neto_prom": neto,
        "peor_mes": peor,
    }


def _evaluacion_vacia() -> dict:
    return {
        "estado": "ERROR",
        "nota": "Tabla financiera vacía",
        "dscr": None,
        "ahorro_prom": 0.0,
        "neto_prom": 0.0,
        "peor_mes": 0.0,
    }


def _clasificar_evaluacion(dscr, neto, peor) -> tuple[str, str]:
    if dscr is None:
        estado = "VIABLE" if neto > 0 and peor >= 0 else "NO VIABLE"
        return estado, "Proyecto evaluado sin deuda financiera."
    if dscr >= 1.20 and neto > 0 and peor >= 0:
        return "VIABLE", "Flujo positivo y buena cobertura de deuda."
    if dscr >= 1.00 and neto > 0:
        return "ACEPTABLE", "El proyecto cubre el servicio de deuda."
    if dscr >= 0.80:
        return "MARGINAL", "Cobertura financiera ajustada."
    return "NO VIABLE", "Los ahorros no cubren el servicio de deuda."


def _tir(flujos, guess=0.10) -> float:
    tasa = guess
    for _ in range(100):
        vpn = sum(f / (1 + tasa) ** i for i, f in enumerate(flujos))
        derivada = sum(-i * f / (1 + tasa) ** (i + 1) for i, f in enumerate(flujos))
        if abs(derivada) < 1e-10:
            break
        tasa -= vpn / derivada
    return tasa


# ==========================================================
# CONSUMO DEL RESULTADO DE BATERÍA
# ==========================================================

def _escenario_seleccionado(bateria):
    return _leer(bateria, "escenario_seleccionado")


def _energia_final(energia, escenario) -> List[float]:
    valores = _leer(escenario, "energia_util_12m_kwh")
    if valores:
        return list(valores)
    return list(getattr(energia, "energia_util_12m", []) or [])


def _flujos_red_12m(escenario):
    resultado = _leer(escenario, "resultado_tecnico", None)

    if resultado is None:
        return None, None

    compra = _leer(
        resultado,
        "compra_red_con_bateria_12m_kwh",
        None,
    )
    inyeccion = _leer(
        resultado,
        "excedente_con_bateria_12m_kwh",
        None,
    )

    if not compra or len(compra) != 12:
        return None, None

    if not inyeccion or len(inyeccion) != 12:
        return None, None

    return list(compra), list(inyeccion)


def _capex_total(capex_fv, escenario) -> float:
    valor = _float(_leer(escenario, "capex_total_l", 0.0))
    return valor if valor > 0 else capex_fv


def _escenario_a_dict(escenario, tabla, evaluacion) -> dict:
    if escenario is None:
        return {}

    return {
        "nombre": _leer(escenario, "nombre", "Sin batería"),
        "capacidad_bateria_kwh": _float(
            _leer(escenario, "capacidad_bateria_kwh", 0.0)
        ),
        "potencia_bateria_kw": _float(
            _leer(escenario, "potencia_bateria_kw", 0.0)
        ),
        "capex_bateria_L": _float(_leer(escenario, "capex_bateria_l", 0.0)),
        "capex_total_L": _float(_leer(escenario, "capex_total_l", 0.0)),
        "resultado_bateria": _leer(escenario, "resultado_tecnico"),
        "energia_fv_12m_bateria": _leer(escenario, "energia_util_12m_kwh", []),
        "energia_descargada_dia_kwh": _float(
            _leer(escenario, "energia_descargada_dia_kwh", 0.0)
        ),
        "energia_objetivo_kwh": _float(
            _leer(escenario, "energia_objetivo_dia_kwh", 0.0)
        ),
        "tabla_12m": tabla,
        "evaluacion": evaluacion,
        "ahorro_anual_L": sum(fila["ahorro_L"] for fila in tabla),
    }


def _escenarios_compatibles(bateria) -> List[dict]:
    return [
        _escenario_a_dict(escenario, [], {})
        for escenario in (_leer(bateria, "escenarios", []) or [])
    ]


# ==========================================================
# ENTRADA PRINCIPAL
# ==========================================================

def ejecutar_finanzas(
    *,
    datos: Datosproyecto,
    sizing: ResultadoSizing,
    energia: EnergiaResultado,
    bateria=None,
) -> Dict[str, Any]:
    _validar_entrada(sizing, energia)

    contexto = _calcular_contexto(
        datos=datos,
        sizing=sizing,
        energia=energia,
        bateria=bateria,
    )
    return _armar_resultado(**contexto)


def _calcular_contexto(*, datos, sizing, energia, bateria) -> dict:

    perfil = obtener_perfil_financiamiento(datos)
    capex_fv = calcular_capex_L(
        sizing.pdc_kw,
        datos.costo_usd_kwp,
        datos.tcambio,
    )

    escenario = _escenario_seleccionado(bateria)
    capex = _capex_total(capex_fv, escenario)
    energia_12m = _energia_final(energia, escenario)
    compra_red_12m, inyeccion_12m = _flujos_red_12m(
        escenario
    )
    tarifa_inyeccion = _float(
        getattr(datos, "tarifa_inyeccion_l_kwh", 2.72),
        2.72,
    )

    cuota = calcular_cuota_mensual_perfil(capex_L_=capex, perfil=perfil)
    om = om_mensual(capex, datos.om_anual_pct)
    tabla = simular_12_meses(
        consumo_12m=datos.consumo_12m,
        energia_fv_12m=energia_12m,
        tarifa_energia=datos.tarifa_energia,
        cargos_fijos=datos.cargos_fijos,
        cuota_mensual=cuota,
        om_mensual_val=om,
        compra_red_12m=compra_red_12m,
        inyeccion_12m=inyeccion_12m,
        tarifa_inyeccion=tarifa_inyeccion,
    )

    evaluacion = _evaluacion_mensual(tabla, cuota)
    ahorro_anual = sum(fila["ahorro_L"] for fila in tabla)
    detalle = calcular_detalle_financiamiento(capex_L_=capex, perfil=perfil)
    bateria_optima = _escenario_a_dict(escenario, tabla, evaluacion)

    return locals()


def _validar_entrada(sizing, energia) -> None:
    if _float(getattr(sizing, "pdc_kw", 0.0)) <= 0:
        raise ValueError("Sizing incompleto para finanzas.")
    if energia is None or not getattr(energia, "ok", False):
        raise ValueError("Resultado energético inválido.")


def _metricas(capex, ahorro_anual) -> dict:
    roi = ahorro_anual / capex * 100.0 if capex > 0 else 0.0
    payback = capex / ahorro_anual if ahorro_anual > 0 else None
    flujos = [-capex] + [ahorro_anual] * 10
    tir = _tir(flujos) * 100.0 if ahorro_anual > 0 else 0.0
    return {"roi_pct": roi, "payback_anios": payback, "tir_pct": tir}


def _armar_resultado(**ctx) -> Dict[str, Any]:
    escenario = ctx["escenario"]
    perfil = ctx["perfil"]
    detalle = ctx["detalle"]
    tabla = ctx["tabla"]
    ahorro = ctx["ahorro_anual"]
    capex = ctx["capex"]

    consumo_anual_kwh = sum(
        fila["consumo_kwh"]
        for fila in tabla
    )
    energia_fv_util_anual_kwh = sum(
        fila["fv_kwh"]
        for fila in tabla
    )

    cobertura_real = (
        energia_fv_util_anual_kwh / consumo_anual_kwh * 100.0
        if consumo_anual_kwh > 0
        else 0.0
    )

    credito_inyeccion = sum(
        fila.get("credito_inyeccion_aplicado_L", 0.0)
        for fila in tabla
    )
    credito_generado = sum(
        fila.get("credito_inyeccion_generado_L", 0.0)
        for fila in tabla
    )
    ahorro_autoconsumo = max(
        ahorro - credito_inyeccion,
        0.0,
    )

    resultado = {
        "capex_L": capex,
        "capex_total_L": capex,
        "capex_fv_L": ctx["capex_fv"],
        "capex_bateria_L": _float(
            _leer(escenario, "capex_bateria_l", 0.0)
        ),
        "capacidad_bateria_kwh": _float(
            _leer(escenario, "capacidad_bateria_kwh", 0.0)
        ),
        "potencia_bateria_kw": _float(
            _leer(escenario, "potencia_bateria_kw", 0.0)
        ),
        "costo_bateria_usd_kwh": _float(
            getattr(
                ctx["datos"],
                "costo_bateria_usd_kwh",
                0.0,
            )
        ),

        # Energía y cobertura
        "consumo_anual_kwh": consumo_anual_kwh,
        "energia_fv_util_anual_kwh": energia_fv_util_anual_kwh,
        "cobertura_real": cobertura_real,

        # Financiamiento
        "cuota_mensual": ctx["cuota"],
        "cuota_mensual_L": ctx["cuota"],

        # Resultados mensuales
        "tabla_12m": tabla,
        "evaluacion": ctx["evaluacion"],

        # Ahorros
        "ahorro_anual_L": ahorro,
        "ahorro_autoconsumo_anual_L": ahorro_autoconsumo,
        "credito_inyeccion_anual_L": credito_inyeccion,
        "credito_inyeccion_generado_anual_L": credito_generado,
        "saldo_credito_final_L": (
            tabla[-1].get("saldo_credito_L", 0.0)
            if tabla
            else 0.0
        ),

        **detalle,
        **_metricas(capex, ahorro),
    }

    resultado.update(_salida_bateria(ctx))
    resultado.update(_salida_financiamiento(perfil))

    return resultado


def _salida_bateria(ctx) -> dict:
    escenarios = _escenarios_compatibles(ctx["bateria"])
    mejor = ctx["bateria_optima"]
    return {
        "optimizacion_bateria": {"escenarios": escenarios, "mejor": mejor},
        "escenarios_bateria": escenarios,
        "bateria_optima": mejor,
    }


def _salida_financiamiento(perfil) -> dict:
    return {
        "financiamiento": perfil,
        "modo_financiamiento": perfil.get("modo_financiamiento"),
        "nombre_financiamiento": perfil.get("nombre"),
        "entidad_financiera": perfil.get("entidad"),
        "nota_financiamiento": perfil.get("nota"),
        "tasa_anual": perfil.get("tasa_anual"),
        "cat": perfil.get("cat"),
        "plazo_anios": perfil.get("plazo_anios"),
        "plazo_meses": perfil.get("plazo_meses"),
    }
