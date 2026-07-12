# -*- coding: utf-8 -*-
from __future__ import annotations

from energy.baterias.modelos import ConfigBateria
from energy.baterias.balance_bateria import (
    simular_balance_bateria_24h,
)
from energy.baterias.perfiles import (
    preparar_perfiles_bateria,
)
from energy.baterias.recomendador_bateria import (
    generar_opciones_bateria,
)


def ejecutar_bateria(
    demanda_24h,
    fv_24h,
    cfg_bateria: ConfigBateria,
    consumo_anual_kwh: float | None = None,
):
    """
    Simula una batería con perfiles preparados internamente.

    La demanda se normaliza solamente para este módulo.
    No modifica los datos generales del proyecto.
    """

    perfiles = preparar_perfiles_bateria(
        demanda_24h=demanda_24h,
        fv_24h=fv_24h,
        consumo_anual_kwh=consumo_anual_kwh,
    )

    return simular_balance_bateria_24h(
        demanda_24h_kwh=perfiles["demanda_24h"],
        fv_24h_kwh=perfiles["fv_24h"],
        cfg=cfg_bateria,
    )


def ejecutar_recomendacion_bateria(
    demanda_24h,
    fv_24h,
    factor_aprovechamiento: float = 0.80,
    consumo_anual_kwh: float | None = None,
):
    """
    Genera opciones técnicas de batería.

    La preparación y normalización de los perfiles permanece
    dentro del módulo de baterías.
    """

    perfiles = preparar_perfiles_bateria(
        demanda_24h=demanda_24h,
        fv_24h=fv_24h,
        consumo_anual_kwh=consumo_anual_kwh,
    )

    return generar_opciones_bateria(
        demanda_24h=perfiles["demanda_24h"],
        fv_24h=perfiles["fv_24h"],
        factor_aprovechamiento=factor_aprovechamiento,
    )
