from __future__ import annotations

"""
RESULTADO DEL DOMINIO CLIMA — FV Engine

Responsabilidad
---------------
Representar el estado climático horario utilizado por el
motor energético fotovoltaico.

Este resultado es producido por:

    lector_pvgis
    clima_tmy
    generador_clima_base

y consumido por:

    solar.simulacion_8760

Contiene el clima horario del año (8760 registros).
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime


# ==========================================================
# ESTADO CLIMÁTICO DE UNA HORA
# ==========================================================

@dataclass(frozen=True)
class ClimaHora:
    """
    Condiciones climáticas en una hora específica.
    """

    timestamp: datetime

    ghi_wm2: float
    dni_wm2: float
    dhi_wm2: float

    temp_amb_c: float
    viento_ms: float


# ==========================================================
# RESULTADO COMPLETO DEL CLIMA
# ==========================================================

@dataclass(frozen=True)
class ResultadoClima:
    """
    Resultado completo del dominio clima.

    Contiene los datos climáticos horarios necesarios
    para la simulación solar del sistema FV.
    """

    latitud: float
    longitud: float

    horas: List[ClimaHora]


# ==========================================================
# VALIDADOR
# ==========================================================
def validar_clima_8760(clima: ResultadoClima) -> None:

    if not clima.horas:
        raise ValueError("ResultadoClima no contiene horas")

    if len(clima.horas) != 8760:
        raise ValueError(
            f"Se esperaban 8760 horas, pero hay {len(clima.horas)}"
        )

    # 🔴 VALIDACIÓN CRÍTICA
    ghi_total = sum(h.ghi_wm2 for h in clima.horas)

    if ghi_total <= 0:
        raise ValueError("Clima inválido: GHI total = 0")

    # opcional: validar DNI también
    dni_total = sum(h.dni_wm2 for h in clima.horas)

    if dni_total <= 0:
        raise ValueError("Clima inválido: DNI total = 0")ValueError("ResultadoClima no contiene horas")

    if len(clima.horas) != 8760:
        raise ValueError(
            f"Se esperaban 8760 horas de clima, pero se recibieron {len(clima.horas)}"
        )
