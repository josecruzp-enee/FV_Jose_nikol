# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class BateriaRecomendada:
    capacidad_util_kwh: float
    potencia_max_kw: float
    excedente_diario_kwh: float
    consumo_nocturno_kwh: float
    energia_objetivo_kwh: float

    # Evaluación económica
    beneficio_kwh_hnl: float
    ahorro_diario_hnl: float
    ahorro_anual_hnl: float
    capex_bateria_hnl: float
    payback_anios: float | None
    conviene: bool

    criterio: str


def _to_24h_lista(valores) -> List[float]:
    if valores is None:
        return [0.0] * 24

    if isinstance(valores, dict):
        return [float(valores.get(h, 0.0) or 0.0) for h in range(24)]

    if isinstance(valores, (list, tuple)):
        data = [float(x or 0.0) for x in valores]
        if len(data) >= 24:
            return data[:24]
        return data + [0.0] * (24 - len(data))

    return [0.0] * 24


def _redondear_bateria_comercial(kwh: float) -> float:
    if kwh <= 0:
        return 0.0
    if kwh <= 5:
        return 5.0
    if kwh <= 10:
        return 10.0
    if kwh <= 15:
        return 15.0
    if kwh <= 20:
        return 20.0
    if kwh <= 30:
        return 30.0
    return 40.0


def calcular_bateria_recomendada(
    demanda_24h,
    fv_24h,
    factor_aprovechamiento: float = 0.80,

    # Económicos
    costo_bateria_usd_kwh: float = 250.0,
    precio_energia_red_hnl_kwh: float = 5.0,
    precio_inyeccion_hnl_kwh: float = 2.20,
    tipo_cambio_hnl_usd: float = 26.61,
    payback_max_anios: float = 7.0,
) -> BateriaRecomendada:
    demanda = _to_24h_lista(demanda_24h)
    fv = _to_24h_lista(fv_24h)

    excedente_diario = 0.0
    consumo_nocturno = 0.0

    for h in range(24):
        carga = demanda[h]
        gen = fv[h]

        excedente_diario += max(gen - carga, 0.0)

        if h >= 18 or h <= 5:
            consumo_nocturno += carga

    energia_objetivo = min(excedente_diario, consumo_nocturno)
    energia_objetivo *= float(factor_aprovechamiento or 0.80)

    capacidad = _redondear_bateria_comercial(energia_objetivo)

    if capacidad <= 0:
        potencia = 0.0
    elif capacidad <= 5:
        potencia = 3.0
    elif capacidad <= 10:
        potencia = 4.0
    elif capacidad <= 20:
        potencia = 5.0
    else:
        potencia = 10.0

    # =====================================================
    # EVALUACIÓN ECONÓMICA SIMPLE
    # =====================================================
    beneficio_kwh = float(precio_energia_red_hnl_kwh or 0.0) - float(
        precio_inyeccion_hnl_kwh or 0.0
    )

    if beneficio_kwh < 0:
        beneficio_kwh = 0.0

    ahorro_diario = capacidad * beneficio_kwh
    ahorro_anual = ahorro_diario * 365.0

    capex_bateria_hnl = (
        capacidad
        * float(costo_bateria_usd_kwh or 0.0)
        * float(tipo_cambio_hnl_usd or 0.0)
    )

    if ahorro_anual > 0:
        payback = capex_bateria_hnl / ahorro_anual
    else:
        payback = None

    conviene = (
        capacidad > 0
        and payback is not None
        and payback <= float(payback_max_anios or 7.0)
    )

    if capacidad <= 0:
        criterio = (
            "No se recomienda batería porque no se identificó excedente FV "
            "aprovechable o consumo nocturno suficiente."
        )
    elif not conviene:
        criterio = (
            "La batería es técnicamente posible, pero económicamente no se "
            "recomienda bajo los parámetros actuales. El beneficio por kWh "
            "almacenado se calcula como la diferencia entre el precio de energía "
            "comprada a la red y el precio reconocido por inyección."
        )
    else:
        criterio = (
            "La capacidad recomendada se calcula tomando el menor valor entre "
            "excedente FV diario y consumo nocturno, aplicando un factor de "
            "aprovechamiento del 80%, redondeando a una capacidad comercial y "
            "validando que el ahorro estimado genere un payback aceptable."
        )

    return BateriaRecomendada(
        capacidad_util_kwh=capacidad,
        potencia_max_kw=potencia,
        excedente_diario_kwh=excedente_diario,
        consumo_nocturno_kwh=consumo_nocturno,
        energia_objetivo_kwh=energia_objetivo,
        beneficio_kwh_hnl=beneficio_kwh,
        ahorro_diario_hnl=ahorro_diario,
        ahorro_anual_hnl=ahorro_anual,
        capex_bateria_hnl=capex_bateria_hnl,
        payback_anios=payback,
        conviene=conviene,
        criterio=criterio,
    )
