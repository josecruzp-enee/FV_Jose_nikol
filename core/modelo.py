# nucleo/modelo.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Datosproyecto:
    cliente: str
    ubicacion: str

    consumo_12m: List[float]          # 12 meses (kWh)
    tarifa_energia: float             # L/kWh (solo energía)
    cargos_fijos: float               # L/mes

    prod_base_kwh_kwp_mes: float      # ej 145 (kWh/kWp/mes)
    factores_fv_12m: List[float]      # 12 factores (~1.0)
    cobertura_objetivo: float         # 0..1 (típico 0.60–0.80)

    costo_usd_kwp: float
    tcambio: float

    tasa_anual: float                 # ej 0.16
    plazo_anios: int
    porcentaje_financiado: float      # 0..1

    om_anual_pct: float = 0.0         # ej 0.01 (1% anual CAPEX)
