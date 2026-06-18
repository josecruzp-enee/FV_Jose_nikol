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


def _potencia_bateria_kw(capacidad_kwh: float) -> float:
    if capacidad_kwh <= 0:
        return 0.0
    if capacidad_kwh <= 5:
        return 3.0
    if capacidad_kwh <= 10:
        return 4.0
    if capacidad_kwh <= 20:
        return 5.0
    return 10.0


def generar_opciones_bateria(
    demanda_24h,
    fv_24h,
    factor_aprovechamiento: float = 0.80,
    capacidades_comerciales_kwh: List[float] | None = None,
) -> List[BateriaRecomendada]:
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

    if capacidades_comerciales_kwh is None:
        capacidades_comerciales_kwh = [5.0, 10.0, 15.0, 20.0, 30.0, 40.0]

    opciones: List[BateriaRecomendada] = []

    for capacidad in capacidades_comerciales_kwh:
        capacidad = float(capacidad or 0.0)

        if capacidad <= 0:
            continue

        if capacidad > energia_objetivo:
            continue

        opciones.append(
            BateriaRecomendada(
                capacidad_util_kwh=capacidad,
                potencia_max_kw=_potencia_bateria_kw(capacidad),
                excedente_diario_kwh=excedente_diario,
                consumo_nocturno_kwh=consumo_nocturno,
                energia_objetivo_kwh=energia_objetivo,
                criterio=(
                    "Opción técnicamente válida. La capacidad se limita por el menor valor "
                    "entre excedente FV diario y consumo nocturno, aplicando el factor de "
                    "aprovechamiento definido. La selección económica debe realizarse en el "
                    "módulo financiero."
                ),
            )
        )

    if not opciones:
        opciones.append(
            BateriaRecomendada(
                capacidad_util_kwh=0.0,
                potencia_max_kw=0.0,
                excedente_diario_kwh=excedente_diario,
                consumo_nocturno_kwh=consumo_nocturno,
                energia_objetivo_kwh=energia_objetivo,
                criterio=(
                    "No se generan opciones de batería porque no se identificó excedente FV "
                    "aprovechable o consumo nocturno suficiente."
                ),
            )
        )

    return opciones

