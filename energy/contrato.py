from __future__ import annotations

"""
CONTRATO DEL DOMINIO ENERGÍA — FV Engine
========================================

Define las estructuras formales de entrada y salida del
motor energético fotovoltaico.

Este módulo NO contiene lógica de cálculo.

El motor energético soporta dos modelos:

    1) Modelo mensual basado en HSP
    2) Simulación física horaria (8760)

Consumido por:

    core.aplicacion.orquestador_estudio
    reportes
    finanzas
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Literal


# ==========================================================
# ENTRADA DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaInput:

    # ------------------------------------------------------
    # POTENCIA DEL SISTEMA
    # ------------------------------------------------------

    pdc_instalada_kw: float
    pac_nominal_kw: float

    # ------------------------------------------------------
    # MODO
    # ------------------------------------------------------

    modo_simulacion: Literal["mensual", "8760"] = "8760"

    # ------------------------------------------------------
    # HSP
    # ------------------------------------------------------

    hsp_12m: List[float] | None = None
    dias_mes: List[int] | None = None

    # ------------------------------------------------------
    # ORIENTACIÓN
    # ------------------------------------------------------

    tipo_superficie: str | None = None
    azimut_deg: float | None = None
    azimut_a_deg: float | None = None
    azimut_b_deg: float | None = None
    reparto_pct_a: float | None = None
    hemisferio: str | None = None

    # 🔴 NUEVO (8760 REAL)
    tilt_deg: float | None = None

    # ------------------------------------------------------
    # CLIMA 8760
    # ------------------------------------------------------

    clima: Any | None = None   # ResultadoClima

    # ------------------------------------------------------
    # ARREGLO FV (8760)
    # ------------------------------------------------------

    paneles_por_string: int | None = None
    n_strings_total: int | None = None

    pmax_stc_w: float | None = None
    vmp_stc_v: float | None = None
    voc_stc_v: float | None = None

    coef_pmax_pct_per_c: float | None = None
    coef_voc_pct_per_c: float | None = None
    coef_vmp_pct_per_c: float | None = None

    # ------------------------------------------------------
    # PÉRDIDAS
    # ------------------------------------------------------

    perdidas_dc_pct: float = 0.0
    perdidas_ac_pct: float = 0.0
    sombras_pct: float = 0.0

    # ------------------------------------------------------
    # INVERSOR
    # ------------------------------------------------------

    eficiencia_inversor: float = 0.97
    permitir_clipping: bool = True

    # ------------------------------------------------------
    # AMBIENTE
    # ------------------------------------------------------

    latitud: float | None = None
    longitud: float | None = None
    temp_ambiente_c: float = 25.0


# ==========================================================
# RESULTADO DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado del cálculo energético del sistema FV.

    Contiene resultados mensuales y agregados anuales.
    """

    # ------------------------------------------------------
    # ESTADO DEL CÁLCULO
    # ------------------------------------------------------

    ok: bool

    errores: List[str]


    # ------------------------------------------------------
    # POTENCIAS DEL SISTEMA
    # ------------------------------------------------------

    pdc_instalada_kw: float

    pac_nominal_kw: float

    dc_ac_ratio: float


    # ------------------------------------------------------
    # ENERGÍA MENSUAL
    # ------------------------------------------------------

    # energía DC generada antes de pérdidas
    energia_bruta_12m: List[float]

    # pérdidas totales del sistema
    energia_perdidas_12m: List[float]

    # energía después de pérdidas DC
    energia_despues_perdidas_12m: List[float]

    # energía perdida por clipping del inversor
    energia_clipping_12m: List[float]

    # energía AC final entregada
    energia_util_12m: List[float]


    # ------------------------------------------------------
    # ENERGÍA ANUAL
    # ------------------------------------------------------

    energia_bruta_anual: float

    energia_perdidas_anual: float

    energia_despues_perdidas_anual: float

    energia_clipping_anual: float

    energia_util_anual: float


    # ------------------------------------------------------
    # METADATA
    # ------------------------------------------------------

    meta: Dict[str, Any] = field(default_factory=dict)
