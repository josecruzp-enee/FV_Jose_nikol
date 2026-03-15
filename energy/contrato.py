from __future__ import annotations

"""
CONTRATO DEL DOMINIO ENERGIA — FV Engine

Define las estructuras formales de entrada y salida
del motor energético del sistema FV.

Este módulo NO contiene lógica de cálculo.

Responsabilidad:
    definir contratos de datos para el dominio energía.

Consumido por:
    core.orquestador_estudio
    reportes
    finanzas
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


# ==========================================================
# ENTRADA DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaInput:
    """
    Entrada formal del motor energético.

    Este modelo contiene únicamente variables físicas
    necesarias para calcular la producción energética.

    No depende de UI ni de finanzas.
    """

    # ------------------------------------------------------
    # Potencias del sistema
    # ------------------------------------------------------

    pdc_instalada_kw: float
    pac_nominal_kw: float

    # ------------------------------------------------------
    # Recurso solar
    # ------------------------------------------------------

    # irradiancia mensual promedio
    # unidad: kWh/m²/día
    hsp_12m: List[float]

    # ------------------------------------------------------
    # Parámetros físicos
    # ------------------------------------------------------

    dias_mes: List[int]

    # ------------------------------------------------------
    # Factores del sistema
    # ------------------------------------------------------

    factor_orientacion: float

    perdidas_dc_pct: float
    perdidas_ac_pct: float
    sombras_pct: float

    # ------------------------------------------------------
    # Control de clipping
    # ------------------------------------------------------

    permitir_curtailment: bool = True


# ==========================================================
# RESULTADO DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado formal del motor energético FV.
    """

    # estado del cálculo
    ok: bool
    errores: List[str]

    # ------------------------------------------------------
    # Potencias del sistema
    # ------------------------------------------------------

    pdc_instalada_kw: float
    pac_nominal_kw: float

    dc_ac_ratio: float

    # ------------------------------------------------------
    # Energía mensual
    # ------------------------------------------------------

    energia_bruta_12m: List[float]

    energia_despues_perdidas_12m: List[float]

    energia_curtailment_12m: List[float]

    energia_util_12m: List[float]

    # ------------------------------------------------------
    # Energía anual
    # ------------------------------------------------------

    energia_bruta_anual: float

    energia_util_anual: float

    energia_curtailment_anual: float

    # ------------------------------------------------------
    # Metadata adicional
    # ------------------------------------------------------

    meta: Dict[str, Any] = field(default_factory=dict)
