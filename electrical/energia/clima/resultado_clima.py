from __future__ import annotations

"""
CONTRATO DEL DOMINIO CLIMA — FV Engine

Define las estructuras oficiales de datos climáticos
utilizadas por el motor energético del sistema.
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime


# ==========================================================
# DATOS CLIMÁTICOS POR HORA
# ==========================================================

@dataclass(frozen=True)
class ClimaHora:
    """
    Datos climáticos de una hora específica.
    """

    # timestamp real necesario para posición solar
    timestamp: datetime

    # irradiancia global horizontal
    ghi_wm2: float

    # temperatura ambiente
    temp_amb_c: float


# ==========================================================
# RESULTADO CLIMÁTICO ANUAL
# ==========================================================

@dataclass(frozen=True)
class ResultadoClima:
    """
    Serie climática anual utilizada por el simulador 8760.
    """

    horas: List[ClimaHora]

    latitud: float
    longitud: float

    fuente: str

    meta: dict | None = None


# ==========================================================
# VALIDACIÓN BÁSICA
# ==========================================================

def validar_clima_8760(clima: ResultadoClima) -> None:
    """
    Valida que la serie climática tenga 8760 horas.
    """

    if len(clima.horas) != 8760:

        raise ValueError(
            "La serie climática debe contener exactamente 8760 horas."
        )
