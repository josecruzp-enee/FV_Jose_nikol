# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional

from energy.baterias.entrada_bateria import EntradaBateria
from energy.baterias.resultado_bateria import (
    EscenarioBateria,
    ResultadoBateria,
)


DIAS_MES = [
    31, 28, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31,
]


def _normalizar_12m(
    valores,
    nombre: str,
) -> List[float]:

    if not valores or len(valores) != 12:
        raise ValueError(
            f"{nombre} debe contener 12 valores."
        )

    return [
        max(0.0, float(valor or 0.0))
        for valor in valores
    ]


def energia_descargada_diaria(
    resultado: ResultadoBateria | None,
) -> float:

    if resultado is None:
        return 0.0

    valor = float(
        getattr(
            resultado,
            "energia_descargada_bateria_kwh",
            0.0,
        )
        or 0.0
    )

    if valor > 0:
        return valor

    return sum(
        max(0.0, float(valor or 0.0))
        for valor in (
            getattr(
                resultado,
                "descarga_bateria_24h",
                [],
            )
            or []
        )
    )


def construir_energia_util_12m(
    *,
    entrada: EntradaBateria,
    resultado: ResultadoBateria | None,
) -> List[float]:

    consumo_12m = _normalizar_12m(
        entrada.consumo_12m_kwh,
        "consumo_12m_kwh",
    )

    energia_util_12m = _normalizar_12m(
        entrada.energia_fv_util_12m_kwh,
        "energia_fv_util_12m_kwh",
    )

    energia_generada_12m = (
        _normalizar_12m(
            entrada.energia_fv_generada_12m_kwh,
            "energia_fv_generada_12m_kwh",
        )
        if entrada.energia_fv_generada_12m_kwh
        else energia_util_12m[:]
    )

    descarga_diaria = energia_descargada_diaria(
        resultado
    )

    energia_total: List[float] = []

    for mes in range(12):
        consumo = consumo_12m[mes]
        autoconsumo_directo = energia_util_12m[mes]
        generacion = energia_generada_12m[mes]

        excedente = max(
            generacion - autoconsumo_directo,
            0.0,
        )

        deficit = max(
            consumo - autoconsumo_directo,
            0.0,
        )

        descarga_mes = (
            descarga_diaria *
            DIAS_MES[mes]
        )

        aporte_bateria = min(
            excedente,
            deficit,
            descarga_mes,
        )

        energia_total.append(
            min(
                consumo,
                autoconsumo_directo + aporte_bateria,
            )
        )

    return energia_total


def calcular_capex_bateria_l(
    *,
    capacidad_kwh: float,
    entrada: EntradaBateria,
) -> float:

    return (
        max(0.0, float(capacidad_kwh))
        * entrada.costo_bateria_l_kwh
    )


def calcular_cuota_mensual(
    *,
    capex_total_l: float,
    entrada: EntradaBateria,
) -> float:

    if entrada.modo_financiamiento == "contado":
        return 0.0

    porcentaje = max(
        0.0,
        min(
            1.0,
            float(
                entrada.porcentaje_financiado
                or 0.0
            ),
        ),
    )

    principal = (
        max(0.0, float(capex_total_l))
        * porcentaje
    )

    meses = int(
        entrada.plazo_anios or 0
    ) * 12

    if principal <= 0 or meses <= 0:
        return 0.0

    tasa_mensual = max(
        0.0,
        float(entrada.tasa_anual or 0.0),
    ) / 12.0

    if tasa_mensual <= 0:
        return principal / meses

    return (
        tasa_mensual * principal
    ) / (
        1.0 -
        (1.0 + tasa_mensual) ** (-meses)
    )


def calcular_om_mensual(
    *,
    capex_total_l: float,
    entrada: EntradaBateria,
) -> float:

    return (
        max(0.0, float(capex_total_l))
        * max(0.0, float(entrada.om_anual_pct))
        / 12.0
    )


def simular_finanzas_12m(
    *,
    entrada: EntradaBateria,
    energia_util_12m: List[float],
    cuota_mensual_l: float,
    om_mensual_l: float,
) -> List[Dict[str, float]]:

    consumo_12m = _normalizar_12m(
        entrada.consumo_12m_kwh,
        "consumo_12m_kwh",
    )

    energia_12m = _normalizar_12m(
        energia_util_12m,
        "energia_util_12m",
    )

    tabla: List[Dict[str, float]] = []

    for mes in range(12):
        consumo = consumo_12m[mes]

        energia_cubierta = min(
            consumo,
            energia_12m[mes],
        )

        compra_red = max(
            consumo - energia_cubierta,
            0.0,
        )

        factura_base = (
            consumo *
            entrada.tarifa_compra_l_kwh
            + entrada.cargos_fijos_l_mes
        )

        pago_red = (
            compra_red *
            entrada.tarifa_compra_l_kwh
            + entrada.cargos_fijos_l_mes
        )

        ahorro = factura_base - pago_red

        flujo_neto = (
            ahorro
            - cuota_mensual_l
            - om_mensual_l
        )

        tabla.append({
            "mes": mes + 1,
            "consumo_kwh": consumo,
            "energia_cubierta_kwh": energia_cubierta,
            "compra_red_kwh": compra_red,
            "factura_base_l": factura_base,
            "pago_red_l": pago_red,
            "ahorro_l": ahorro,
            "cuota_l": cuota_mensual_l,
            "om_l": om_mensual_l,
            "flujo_neto_l": flujo_neto,
        })

    return tabla


def _calcular_dscr(
    *,
    tabla_12m: List[Dict[str, float]],
    cuota_mensual_l: float,
) -> Optional[float]:

    if cuota_mensual_l <= 0:
        return None

    ahorro_promedio = sum(
        fila["ahorro_l"]
        for fila in tabla_12m
    ) / 12.0

    return ahorro_promedio / cuota_mensual_l


def evaluar_escenario_bateria(
    *,
    entrada: EntradaBateria,
    nombre: str,
    capacidad_kwh: float,
    potencia_kw: float,
    resultado_tecnico: ResultadoBateria | None,
    energia_objetivo_kwh: float = 0.0,
    escenario_base: EscenarioBateria | None = None,
) -> EscenarioBateria:

    capex_bateria_l = calcular_capex_bateria_l(
        capacidad_kwh=capacidad_kwh,
        entrada=entrada,
    )

    capex_total_l = (
        entrada.capex_fv_l +
        capex_bateria_l
    )

    cuota_mensual_l = calcular_cuota_mensual(
        capex_total_l=capex_total_l,
        entrada=entrada,
    )

    om_mensual_l = calcular_om_mensual(
        capex_total_l=capex_total_l,
        entrada=entrada,
    )

    energia_util_12m = construir_energia_util_12m(
        entrada=entrada,
        resultado=resultado_tecnico,
    )

    tabla_12m = simular_finanzas_12m(
        entrada=entrada,
        energia_util_12m=energia_util_12m,
        cuota_mensual_l=cuota_mensual_l,
        om_mensual_l=om_mensual_l,
    )

    ahorro_anual_l = sum(
        fila["ahorro_l"]
        for fila in tabla_12m
    )

    ahorro_base_l = (
        escenario_base.ahorro_anual_l
        if escenario_base
        else 0.0
    )

    ahorro_incremental_l = max(
        ahorro_anual_l - ahorro_base_l,
        0.0,
    )

    payback_total = (
        capex_total_l / ahorro_anual_l
        if ahorro_anual_l > 0
        else None
    )

    payback_bateria = (
        capex_bateria_l / ahorro_incremental_l
        if capex_bateria_l > 0
        and ahorro_incremental_l > 0
        else None
    )

    roi_total = (
        ahorro_anual_l / capex_total_l * 100.0
        if capex_total_l > 0
        else 0.0
    )

    roi_bateria = (
        ahorro_incremental_l /
        capex_bateria_l * 100.0
        if capex_bateria_l > 0
        else 0.0
    )

    estado = "VIABLE"

    if capacidad_kwh > 0:
        if ahorro_incremental_l <= 0:
            estado = "NO CONVENIENTE"

        elif (
            payback_bateria is None
            or payback_bateria >
            entrada.vida_util_bateria_anios
        ):
            estado = "NO RENTABLE"

    return EscenarioBateria(
        nombre=nombre,
        capacidad_bateria_kwh=capacidad_kwh,
        potencia_bateria_kw=potencia_kw,
        capex_bateria_l=capex_bateria_l,
        capex_total_l=capex_total_l,
        energia_descargada_dia_kwh=(
            energia_descargada_diaria(
                resultado_tecnico
            )
        ),
        energia_objetivo_dia_kwh=(
            energia_objetivo_kwh
        ),
        ahorro_anual_l=ahorro_anual_l,
        ahorro_incremental_anual_l=(
            ahorro_incremental_l
        ),
        cuota_mensual_l=cuota_mensual_l,
        om_mensual_l=om_mensual_l,
        payback_total_anios=payback_total,
        payback_bateria_anios=payback_bateria,
        roi_total_pct=roi_total,
        roi_bateria_pct=roi_bateria,
        dscr=_calcular_dscr(
            tabla_12m=tabla_12m,
            cuota_mensual_l=cuota_mensual_l,
        ),
        estado=estado,
        energia_util_12m_kwh=energia_util_12m,
        tabla_12m=tabla_12m,
        resultado_tecnico=resultado_tecnico,
    )


def seleccionar_mejor_escenario(
    *,
    escenarios: List[EscenarioBateria],
    vida_util_bateria_anios: int,
) -> EscenarioBateria:

    if not escenarios:
        raise ValueError(
            "No existen escenarios de batería."
        )

    escenario_base = next(
        (
            escenario
            for escenario in escenarios
            if escenario.capacidad_bateria_kwh <= 0
        ),
        escenarios[0],
    )

    candidatos = [
        escenario
        for escenario in escenarios
        if (
            escenario.capacidad_bateria_kwh > 0
            and escenario.ahorro_incremental_anual_l > 0
            and escenario.payback_bateria_anios is not None
            and escenario.payback_bateria_anios
            <= vida_util_bateria_anios
        )
    ]

    if not candidatos:
        escenario_base.criterio_seleccion = (
            "Ninguna batería recupera su inversión "
            "dentro de su vida útil."
        )

        return escenario_base

    mejor = max(
        candidatos,
        key=lambda escenario: (
            escenario.ahorro_incremental_anual_l
            - (
                escenario.capex_bateria_l
                / max(vida_util_bateria_anios, 1)
            ),
            -escenario.capex_bateria_l,
        ),
    )

    mejor.criterio_seleccion = (
        "Escenario seleccionado por beneficio económico "
        "incremental y recuperación dentro de la vida útil."
    )

    return mejor
