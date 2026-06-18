# -*- coding: utf-8 -*-
from __future__ import annotations

from energy.baterias.modelos import ConfigBateria
from energy.baterias.balance_bateria import simular_balance_bateria_24h
from energy.baterias.perfiles import promediar_energia_8760_a_24h
from energy.baterias.recomendador import generar_opciones_bateria


def ejecutar_bateria(
    demanda_24h,
    fv_24h,
    cfg_bateria: ConfigBateria,
):
    """
    Punto único de entrada para simular una batería ya definida.

    Recibe:
        demanda_24h
        fv_24h o fv_8760
        configuración batería

    Devuelve:
        ResultadoBateria
    """

    if fv_24h and len(fv_24h) != 24:
        fv_24h = promediar_energia_8760_a_24h(fv_24h)

    return simular_balance_bateria_24h(
        demanda_24h_kwh=demanda_24h,
        fv_24h_kwh=fv_24h,
        cfg=cfg_bateria,
    )


def ejecutar_recomendacion_bateria(
    demanda_24h,
    fv_24h,
    factor_aprovechamiento: float = 0.80,
):
    """
    Genera opciones técnicas de batería.

    No evalúa CAPEX, payback ni conveniencia económica.
    Esa decisión corresponde al módulo financiero.

    Recibe:
        demanda_24h
        fv_24h o fv_8760
        factor_aprovechamiento

    Devuelve:
        List[BateriaRecomendada]
    """

    if fv_24h and len(fv_24h) != 24:
        fv_24h = promediar_energia_8760_a_24h(fv_24h)

    return generar_opciones_bateria(
        demanda_24h=demanda_24h,
        fv_24h=fv_24h,
        factor_aprovechamiento=factor_aprovechamiento,
    )
