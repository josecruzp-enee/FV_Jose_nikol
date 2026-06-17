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

    if capacidad <= 5:
        potencia = 3.0
    elif capacidad <= 10:
        potencia = 5.0
    elif capacidad <= 20:
        potencia = 8.0
    else:
        potencia = 10.0

    return BateriaRecomendada(
        capacidad_util_kwh=capacidad,
        potencia_max_kw=potencia,
        excedente_diario_kwh=excedente_diario,
        consumo_nocturno_kwh=consumo_nocturno,
        energia_objetivo_kwh=energia_objetivo,
        criterio=(
            "La capacidad recomendada se calcula tomando el menor valor entre "
            "excedente FV diario y consumo nocturno, aplicando un factor de "
            "aprovechamiento del 80% y redondeando a una capacidad comercial."
        ),
    )
