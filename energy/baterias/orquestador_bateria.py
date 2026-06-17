# -*- coding: utf-8 -*-
from __future__ import annotations

from energy.baterias.modelos import ConfigBateria
from energy.baterias.balance_bateria import simular_balance_bateria_24h


def ejecutar_bateria(
    demanda_24h,
    fv_24h,
    cfg_bateria: ConfigBateria,
):
    """
    Punto único de entrada para el módulo de baterías.

    Recibe:
        demanda_24h
        fv_24h
        configuración batería

    Devuelve:
        ResultadoBateria
    """

    return simular_balance_bateria_24h(
        demanda_24h_kwh=demanda_24h,
        fv_24h_kwh=fv_24h,
        cfg=cfg_bateria,
    )
