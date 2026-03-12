# core/servicios/consumo.py
from __future__ import annotations

"""
SERVICIO: UTILIDADES DE CONSUMO ENERGETICO

FRONTERA
--------
Capa:
    core.servicios

Consumido por:
    sizing
    analisis_cobertura
    orquestador_estudio

Responsabilidad:
    Calcular métricas básicas de consumo energético.

No debe:
    - ejecutar ingeniería FV
    - simular energía
    - calcular finanzas
    - interactuar con UI

ENTRADA
-------
consumo_12m: List[float]

cobertura: float

SALIDA
------
consumo_anual_kwh(...) -> float
consumo_promedio_mensual_kwh(...) -> float
normalizar_cobertura(...) -> float
"""

from typing import List


# =========================================================
# CONSUMO ANUAL
# =========================================================

def consumo_anual_kwh(consumo_12m: List[float]) -> float:
    """
    Calcula el consumo anual total a partir de 12 meses.
    """

    return float(sum(float(x or 0.0) for x in consumo_12m))


# =========================================================
# PROMEDIO MENSUAL
# =========================================================

def consumo_promedio_mensual_kwh(consumo_12m: List[float]) -> float:
    """
    Calcula el consumo promedio mensual.
    """

    if not consumo_12m:
        return 0.0

    return consumo_anual_kwh(consumo_12m) / 12.0


# =========================================================
# NORMALIZAR COBERTURA
# =========================================================

def normalizar_cobertura(cobertura: float) -> float:
    """
    Limita el valor de cobertura entre 0 y 1.
    """

    return max(0.0, min(1.0, float(cobertura)))
