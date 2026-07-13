# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfigBateria:
    usar_bateria: bool = False

    capacidad_util_kwh: float = 0.0
    potencia_max_kw: float = 0.0

    soc_inicial_pct: float = 20.0
    soc_min_pct: float = 20.0
    soc_max_pct: float = 100.0

    eficiencia_ida_vuelta: float = 0.90

    costo_usd_kwh: float = 200.0
    vida_util_anios: int = 10
