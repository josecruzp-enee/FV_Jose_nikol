# electrical/energia/balance.py

from __future__ import annotations
from typing import List


def consumo_anual_kwh(consumo_12m: List[float]) -> float:
    return float(sum(float(x or 0.0) for x in consumo_12m))


def consumo_promedio_mensual_kwh(consumo_12m: List[float]) -> float:
    if not consumo_12m:
        return 0.0
    return consumo_anual_kwh(consumo_12m) / 12.0


def normalizar_cobertura(cobertura: float) -> float:
    return max(0.0, min(1.0, float(cobertura)))
