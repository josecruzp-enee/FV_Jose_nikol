from __future__ import annotations

"""
CONTRATO DEL DOMINIO ENERGIA — FV Engine

Define las estructuras formales de entrada y salida del
motor energético fotovoltaico.

Este módulo NO contiene lógica de cálculo.

Responsabilidad
---------------
Definir los contratos de datos utilizados por el dominio
energía para ejecutar los modelos energéticos del sistema FV.

El motor energético soporta dos modos de simulación:

    1) Modelo energético mensual (HSP)
    2) Simulación física horaria (8760)

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
    Entrada formal del motor energético FV.

    Este modelo agrupa todos los parámetros físicos
    necesarios para ejecutar cualquiera de los dos
    modelos energéticos disponibles:

        • modelo mensual (HSP)
        • simulación horaria 8760

    El orquestador energético decidirá qué modelo
    ejecutar dependiendo del modo de simulación.
    """

    # ------------------------------------------------------
    # Potencias del sistema FV
    # ------------------------------------------------------

    # potencia DC total instalada (kW)
    pdc_instalada_kw: float

    # potencia AC nominal del inversor (kW)
    pac_nominal_kw: float

    # ------------------------------------------------------
    # Modo de simulación energética
    # ------------------------------------------------------

    # opciones típicas:
    # "mensual" → modelo HSP
    # "8760"    → simulación horaria
    modo_simulacion: str = "mensual"

    # ------------------------------------------------------
    # Recurso solar mensual (modelo HSP)
    # ------------------------------------------------------

    # irradiancia mensual promedio
    # unidades: kWh/m²/día
    hsp_12m: List[float] | None = None

    # número de días por mes
    dias_mes: List[int] | None = None

    # ------------------------------------------------------
    # Parámetros geográficos (modelo 8760)
    # ------------------------------------------------------

    latitud: float | None = None
    longitud: float | None = None

    # ------------------------------------------------------
    # Factores del sistema FV
    # ------------------------------------------------------

    # factor energético por orientación del generador
    factor_orientacion: float = 1.0

    # pérdidas DC del sistema (cables, mismatch, etc.)
    perdidas_dc_pct: float = 0.0

    # pérdidas AC del sistema
    perdidas_ac_pct: float = 0.0

    # pérdidas por sombras
    sombras_pct: float = 0.0

    # ------------------------------------------------------
    # Control de clipping del inversor
    # ------------------------------------------------------

    permitir_curtailment: bool = True

    # ------------------------------------------------------
    # Parámetros térmicos simplificados
    # ------------------------------------------------------

    # temperatura ambiente promedio (usada en modelos simplificados)
    temp_ambiente_c: float = 25.0


# ==========================================================
# RESULTADO DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado formal del motor energético FV.

    Contiene la producción energética del sistema
    tanto a nivel mensual como anual.
    """

    # ------------------------------------------------------
    # estado del cálculo
    # ------------------------------------------------------

    ok: bool
    errores: List[str]

    # ------------------------------------------------------
    # Potencias del sistema
    # ------------------------------------------------------

    pdc_instalada_kw: float
    pac_nominal_kw: float

    # relación DC/AC del sistema
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
