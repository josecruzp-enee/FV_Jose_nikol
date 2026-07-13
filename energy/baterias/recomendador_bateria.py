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


def _to_lista(valores) -> List[float]:
    if valores is None:
        return []

    if isinstance(valores, dict):
        return [
            max(
                0.0,
                float(
                    valores.get(
                        hora,
                        valores.get(str(hora), 0.0),
                    )
                    or 0.0
                ),
            )
            for hora in range(24)
        ]

    if isinstance(valores, (list, tuple)):
        return [
            max(0.0, float(valor or 0.0))
            for valor in valores
        ]

    return []


def _validar_perfiles(demanda, fv) -> None:
    if len(demanda) not in (24, 8760, 8784):
        raise ValueError(
            "La demanda debe contener 24, 8760 o 8784 valores."
        )

    if len(fv) != len(demanda):
        raise ValueError(
            "La demanda y la generación FV deben tener igual longitud."
        )


def _potencia_bateria_kw(
    capacidad_kwh: float,
) -> float:
    """
    Potencia máxima estimada usando una tasa de descarga de 0.5 C.

    Ejemplo:
        25 kWh × 0.5 = 12.5 kW
    """

    capacidad = max(
        0.0,
        float(capacidad_kwh or 0.0),
    )

    return capacidad * 0.5
def _indicadores_diarios(demanda, fv):
    dias = len(demanda) / 24.0
    excedente_total = 0.0
    consumo_nocturno_total = 0.0

    for indice, (carga, gen) in enumerate(zip(demanda, fv)):
        excedente_total += max(gen - carga, 0.0)

        hora = indice % 24
        if hora >= 18 or hora <= 5:
            consumo_nocturno_total += carga

    if dias <= 0:
        return 0.0, 0.0

    return (
        excedente_total / dias,
        consumo_nocturno_total / dias,
    )


def generar_opciones_bateria(
    demanda_24h,
    fv_24h,
    factor_aprovechamiento: float = 0.80,
    capacidades_comerciales_kwh: List[float] | None = None,
) -> List[BateriaRecomendada]:
    """
    Genera candidatos técnicos para la simulación.

    Los nombres de los argumentos se conservan por compatibilidad,
    pero pueden recibir perfiles de 24, 8760 o 8784 valores.
    La selección final se realiza con la simulación económica anual.
    """

    demanda = _to_lista(demanda_24h)
    fv = _to_lista(fv_24h)
    _validar_perfiles(demanda, fv)

    excedente_diario, consumo_nocturno = _indicadores_diarios(
        demanda,
        fv,
    )
    factor = max(
        0.0,
        min(1.0, float(factor_aprovechamiento or 0.80)),
    )
    energia_objetivo = (
        min(excedente_diario, consumo_nocturno)
        * factor
    )

    if capacidades_comerciales_kwh is None:
        capacidades_comerciales_kwh = [
            5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0
        ]

    capacidades = sorted({
        float(capacidad)
        for capacidad in capacidades_comerciales_kwh
        if float(capacidad or 0.0) > 0
    })

    if excedente_diario <= 0 or consumo_nocturno <= 0:
        return [
            BateriaRecomendada(
                capacidad_util_kwh=0.0,
                potencia_max_kw=0.0,
                excedente_diario_kwh=excedente_diario,
                consumo_nocturno_kwh=consumo_nocturno,
                energia_objetivo_kwh=energia_objetivo,
                criterio=(
                    "No se identificó excedente FV aprovechable "
                    "o consumo nocturno suficiente."
                ),
            )
        ]

    return [
        BateriaRecomendada(
            capacidad_util_kwh=capacidad,
            potencia_max_kw=_potencia_bateria_kw(capacidad),
            excedente_diario_kwh=excedente_diario,
            consumo_nocturno_kwh=consumo_nocturno,
            energia_objetivo_kwh=energia_objetivo,
            criterio=(
                "Capacidad comercial candidata. Su desempeño técnico "
                "y económico se evalúa con la simulación anual 8760."
            ),
        )
        for capacidad in capacidades
    ]
