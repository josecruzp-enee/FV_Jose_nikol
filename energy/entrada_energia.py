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
    Compatible con modelo mensual y simulación 8760.
    """

    # ------------------------------------------------------
    # Potencias del sistema
    # ------------------------------------------------------

    pdc_instalada_kw: float
    pac_nominal_kw: float

    # ------------------------------------------------------
    # Recurso solar (modelo mensual)
    # ------------------------------------------------------

    hsp_12m: List[float]
    dias_mes: List[int]

    # ------------------------------------------------------
    # Geometría del sistema
    # ------------------------------------------------------

    factor_orientacion: float

    # ------------------------------------------------------
    # Pérdidas del sistema
    # ------------------------------------------------------

    perdidas_dc_pct: float
    perdidas_ac_pct: float
    sombras_pct: float

    # ------------------------------------------------------
    # Clipping del inversor
    # ------------------------------------------------------

    permitir_curtailment: bool

    # ------------------------------------------------------
    # Modo de simulación
    # ------------------------------------------------------

    modo_simulacion: str = "mensual"

    # ------------------------------------------------------
    # Parámetros geográficos (necesarios para 8760)
    # ------------------------------------------------------

    latitud: float | None = None
    longitud: float | None = None

    # ------------------------------------------------------
    # Temperatura ambiente promedio
    # ------------------------------------------------------

    temp_ambiente_c: float = 25.0
