from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ==========================================================
# ENTRADA DEL DOMINIO ENERGIA
# ==========================================================

@dataclass(frozen=True)
class EnergiaInput:
    """
    Parámetros de entrada del motor energético FV.
    """

    # Potencias del sistema
    pdc_instalada_kw: float
    pac_nominal_kw: float

    # Recurso solar
    hsp_12m: List[float]

    # Días por mes
    dias_mes: List[int]

    # Factor de orientación del generador
    factor_orientacion: float

    # Pérdidas del sistema
    perdidas_dc_pct: float
    perdidas_ac_pct: float
    sombras_pct: float

    # Control de clipping
    permitir_curtailment: bool
