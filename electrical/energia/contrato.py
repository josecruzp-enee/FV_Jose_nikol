# electrical/energia/contrato.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True)
class EnergiaInput:
    """
    Entrada formal del motor energético.
    No depende de finanzas.
    No depende de UI.
    Solo física del sistema.
    """

    # Potencias
    pdc_instalada_kw: float
    pac_nominal_kw: float

    # Irradiancia mensual (kWh/m2/día)
    hsp_12m: List[float]

    # Parámetros físicos
    dias_mes: List[int]

    # Factores físicos
    factor_orientacion: float
    perdidas_dc_pct: float
    perdidas_ac_pct: float
    sombras_pct: float

    # Control futuro
    permitir_curtailment: bool = True


@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado formal del motor energético.
    """

    ok: bool
    errores: List[str]

    pdc_instalada_kw: float
    pac_nominal_kw: float
    dc_ac_ratio: float

    energia_bruta_12m: List[float]
    energia_despues_perdidas_12m: List[float]
    energia_curtailment_12m: List[float]
    energia_util_12m: List[float]

    energia_bruta_anual: float
    energia_util_anual: float
    energia_curtailment_anual: float

    meta: Dict[str, Any]
