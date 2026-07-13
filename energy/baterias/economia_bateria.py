# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional

from energy.baterias.entrada_bateria import EntradaBateria
from energy.baterias.resultado_bateria import (
    EscenarioBateria,
    ResultadoBateria,
)


def _normalizar_12m(valores, nombre: str) -> List[float]:
    if not valores or len(valores) != 12:
        raise ValueError(f"{nombre} debe contener 12 valores.")

    return [max(0.0, float(valor or 0.0)) for valor in valores]


def energia_descargada_diaria(
    resultado: ResultadoBateria | None,
) -> float:
    if resultado is None:
        return 0.0

    descarga = max(
        0.0,
        float(resultado.energia_descargada_bateria_kwh or 0.0),
    )
    n_horas = len(resultado.descarga_bateria_horaria_kwh)

    if n_horas in (8760, 8784):
        return descarga / (n_horas / 24.0)

    return descarga


def construir_energia_util_12m(
    *,
    entrada: EntradaBateria,
    resultado: ResultadoBateria | None,
) -> List[float]:
    if resultado is None:
        raise ValueError(
            "El escenario económico requiere un resultado técnico."
        )

    demanda = _normalizar_12m(
        resultado.demanda_12m_kwh,
        "demanda_12m_kwh",
    )
    compra = _normalizar_12m(
        resultado.compra_red_con_bateria_12m_kwh,
        "compra_red_con_bateria_12m_kwh",
    )

    return [
        max(0.0, demanda_mes - compra_mes)
        for demanda_mes, compra_mes in zip(demanda, compra)
    ]


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
        min(1.0, float(entrada.porcentaje_financiado or 0.0)),
    )
    principal = max(0.0, float(capex_total_l)) * porcentaje
    meses = int(entrada.plazo_anios or 0) * 12

    if principal <= 0 or meses <= 0:
        return 0.0

    tasa_mensual = max(
        0.0,
        float(entrada.tasa_anual or 0.0),
    ) / 12.0

    if tasa_mensual <= 0:
        return principal / meses

    return tasa_mensual * principal / (
        1.0 - (1.0 + tasa_mensual) ** (-meses)
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
    resultado: ResultadoBateria,
    cuota_mensual_l: float,
    om_mensual_l: float,
) -> List[Dict[str, float]]:
    demanda = _normalizar_12m(
        resultado.demanda_12m_kwh,
        "demanda_12m_kwh",
    )
    compra = _normalizar_12m(
        resultado.compra_red_con_bateria_12m_kwh,
        "compra_red_con_bateria_12m_kwh",
    )
    inyeccion = _normalizar_12m(
        resultado.excedente_con_bateria_12m_kwh,
        "excedente_con_bateria_12m_kwh",
    )

    tabla: List[Dict[str, float]] = []

    for mes in range(12):
        factura_base = (
            demanda[mes] * entrada.tarifa_compra_l_kwh
            + entrada.cargos_fijos_l_mes
        )
        costo_compra = compra[mes] * entrada.tarifa_compra_l_kwh
        ingreso_inyeccion = (
            inyeccion[mes] * entrada.tarifa_inyeccion_l_kwh
        )
        pago_neto_red = (
            costo_compra
            + entrada.cargos_fijos_l_mes
            - ingreso_inyeccion
        )
        ahorro = factura_base - pago_neto_red
        flujo_antes_deuda = ahorro - om_mensual_l
        flujo_neto = flujo_antes_deuda - cuota_mensual_l

        tabla.append({
            "mes": mes + 1,
            "consumo_kwh": demanda[mes],
            "energia_cubierta_kwh": max(
                0.0,
                demanda[mes] - compra[mes],
            ),
            "compra_red_kwh": compra[mes],
            "inyeccion_red_kwh": inyeccion[mes],
            "factura_base_l": factura_base,
            "costo_compra_red_l": costo_compra,
            "ingreso_inyeccion_l": ingreso_inyeccion,
            "pago_red_l": pago_neto_red,
            "ahorro_l": ahorro,
            "cuota_l": cuota_mensual_l,
            "om_l": om_mensual_l,
            "flujo_antes_deuda_l": flujo_antes_deuda,
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

    flujo_disponible = sum(
        fila["flujo_antes_deuda_l"]
        for fila in tabla_12m
    ) / 12.0

    return flujo_disponible / cuota_mensual_l


def _totales_red(tabla_12m):
    costo_compra = sum(
        fila["costo_compra_red_l"]
        for fila in tabla_12m
    )
    ingreso_inyeccion = sum(
        fila["ingreso_inyeccion_l"]
        for fila in tabla_12m
    )

    return costo_compra, ingreso_inyeccion


def _estado_escenario(
    *,
    capacidad_kwh,
    ahorro_incremental,
    payback_bateria,
    vida_util,
    dscr,
):
    if capacidad_kwh <= 0:
        return "VIABLE"

    if ahorro_incremental <= 0:
        return "NO CONVENIENTE"

    if payback_bateria is None:
        return "NO RENTABLE"

    limite_observacion = vida_util * 1.30

    if payback_bateria > limite_observacion:
        return "NO RENTABLE"

    if dscr is not None and dscr < 1.0:
        return "NO AUTOSOSTENIBLE"

    if payback_bateria > vida_util:
        return "VIABLE CON OBSERVACIONES"

    if dscr is not None and dscr < 1.20:
        return "COBERTURA AJUSTADA"

    return "RENTABLE"

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
    if resultado_tecnico is None:
        raise ValueError(
            "El escenario requiere una simulación técnica 8760."
        )

    capex_bateria_l = calcular_capex_bateria_l(
        capacidad_kwh=capacidad_kwh,
        entrada=entrada,
    )
    capex_total_l = entrada.capex_fv_l + capex_bateria_l
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
        resultado=resultado_tecnico,
        cuota_mensual_l=cuota_mensual_l,
        om_mensual_l=om_mensual_l,
    )

    ahorro_anual_l = sum(fila["ahorro_l"] for fila in tabla_12m)
    ahorro_base_l = escenario_base.ahorro_anual_l if escenario_base else 0.0
    om_base_anual = (
        escenario_base.om_mensual_l * 12.0
        if escenario_base else 0.0
    )
    om_incremental_anual = max(
        om_mensual_l * 12.0 - om_base_anual,
        0.0,
    )
    ahorro_incremental_l = (
        0.0
        if escenario_base is None
        else (
            ahorro_anual_l
            - ahorro_base_l
            - om_incremental_anual
        )
    )
    ahorro_neto_total_l = ahorro_anual_l - om_mensual_l * 12.0

    payback_total = (
        capex_total_l / ahorro_neto_total_l
        if ahorro_neto_total_l > 0 else None
    )
    payback_bateria = (
        capex_bateria_l / ahorro_incremental_l
        if capex_bateria_l > 0 and ahorro_incremental_l > 0
        else None
    )
    roi_total = (
        ahorro_neto_total_l / capex_total_l * 100.0
        if capex_total_l > 0 else 0.0
    )
    roi_bateria = (
        ahorro_incremental_l / capex_bateria_l * 100.0
        if capex_bateria_l > 0 else 0.0
    )
    dscr = _calcular_dscr(
        tabla_12m=tabla_12m,
        cuota_mensual_l=cuota_mensual_l,
    )
    costo_compra, ingreso_inyeccion = _totales_red(tabla_12m)
    costo_base = (
        escenario_base.costo_red_con_bateria_anual_l
        if escenario_base else costo_compra
    )
    ingreso_base = (
        escenario_base.ingreso_inyeccion_con_bateria_anual_l
        if escenario_base else ingreso_inyeccion
    )

    estado = _estado_escenario(
        capacidad_kwh=capacidad_kwh,
        ahorro_incremental=ahorro_incremental_l,
        payback_bateria=payback_bateria,
        vida_util=entrada.vida_util_bateria_anios,
        dscr=dscr,
    )

    return EscenarioBateria(
        nombre=nombre,
        capacidad_bateria_kwh=capacidad_kwh,
        potencia_bateria_kw=potencia_kw,
        capex_bateria_l=capex_bateria_l,
        capex_total_l=capex_total_l,
        energia_descargada_dia_kwh=energia_descargada_diaria(
            resultado_tecnico
        ),
        energia_objetivo_dia_kwh=energia_objetivo_kwh,
        ahorro_anual_l=ahorro_anual_l,
        ahorro_incremental_anual_l=ahorro_incremental_l,
        costo_red_sin_bateria_anual_l=costo_base,
        costo_red_con_bateria_anual_l=costo_compra,
        ingreso_inyeccion_sin_bateria_anual_l=ingreso_base,
        ingreso_inyeccion_con_bateria_anual_l=ingreso_inyeccion,
        cuota_mensual_l=cuota_mensual_l,
        om_mensual_l=om_mensual_l,
        payback_total_anios=payback_total,
        payback_bateria_anios=payback_bateria,
        roi_total_pct=roi_total,
        roi_bateria_pct=roi_bateria,
        dscr=dscr,
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
        raise ValueError("No existen escenarios de batería.")

    escenario_base = next(
        (
            escenario
            for escenario in escenarios
            if escenario.capacidad_bateria_kwh <= 0
        ),
        escenarios[0],
    )

    limite_observacion = vida_util_bateria_anios * 1.30

    candidatos_rentables = [
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

    candidatos_observados = [
        escenario
        for escenario in escenarios
        if (
            escenario.capacidad_bateria_kwh > 0
            and escenario.ahorro_incremental_anual_l > 0
            and escenario.payback_bateria_anios is not None
            and vida_util_bateria_anios
            < escenario.payback_bateria_anios
            <= limite_observacion
        )
    ]

    if candidatos_rentables:
        mejor = max(
            candidatos_rentables,
            key=lambda escenario: (
                escenario.ahorro_incremental_anual_l
                - escenario.capex_bateria_l
                / max(vida_util_bateria_anios, 1),
                -escenario.capex_bateria_l,
            ),
        )
        mejor.criterio_seleccion = (
            "Batería seleccionada por beneficio económico incremental "
            "y recuperación dentro de su vida útil."
        )
        return mejor

    if candidatos_observados:
        mejor = max(
            candidatos_observados,
            key=lambda escenario: (
                escenario.ahorro_incremental_anual_l,
                -escenario.payback_bateria_anios,
            ),
        )
        mejor.criterio_seleccion = (
            "Alternativa técnicamente aprovechable seleccionada con "
            "observaciones económicas. Su recuperación estimada supera "
            "la vida útil de referencia, pero permanece dentro del margen "
            "de evaluación del 30%."
        )
        return mejor

    escenario_base.criterio_seleccion = (
        "Ninguna batería presenta ahorro y recuperación dentro del "
        "margen económico máximo evaluado."
    )
    return escenario_base


def seleccionar_escenario_tecnico(
    *,
    escenarios: List[EscenarioBateria],
) -> EscenarioBateria | None:
    """
    Selecciona una alternativa técnica sin convertirla en recomendación
    económica.

    Prioriza la batería de menor capacidad que alcance la energía objetivo
    diaria. Si ninguna la alcanza, devuelve la que entregue mayor energía
    diaria, indicando que la recuperación es parcial.
    """
    candidatos = [
        escenario
        for escenario in escenarios
        if (
            escenario.capacidad_bateria_kwh > 0
            and escenario.resultado_tecnico is not None
        )
    ]

    if not candidatos:
        return None

    objetivo = max(
        float(escenario.energia_objetivo_dia_kwh or 0.0)
        for escenario in candidatos
    )

    que_cumplen = [
        escenario
        for escenario in candidatos
        if (
            objetivo > 0
            and escenario.energia_descargada_dia_kwh >= objetivo
        )
    ]

    if que_cumplen:
        seleccionado = min(
            que_cumplen,
            key=lambda escenario: (
                escenario.capacidad_bateria_kwh,
                escenario.capex_bateria_l,
            ),
        )
        seleccionado.criterio_seleccion = (
            "Alternativa técnica de menor capacidad que alcanza la energía "
            "objetivo diaria. Su factibilidad económica debe evaluarse por "
            "separado."
        )
        return seleccionado

    seleccionado = max(
        candidatos,
        key=lambda escenario: (
            escenario.energia_descargada_dia_kwh,
            -escenario.capacidad_bateria_kwh,
        ),
    )
    seleccionado.criterio_seleccion = (
        "Alternativa técnica con mayor recuperación entre las capacidades "
        "evaluadas. No alcanza completamente la energía objetivo diaria."
    )
    return seleccionado
