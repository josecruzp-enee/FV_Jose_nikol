from __future__ import annotations

"""
RESULTADO DEL DOMINIO CLIMA — FV Engine
"""

from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime


# ==========================================================
# ESTADO CLIMÁTICO DE UNA HORA
# ==========================================================

@dataclass(frozen=True)
class ClimaHora:
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

    latitud: float
    longitud: float

    horas: List[ClimaHora]

    # 👇 opcional pero clave
    fuente: str = "desconocido"
    meta: Dict[str, object] = None


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

    ghi_total = 0.0
    dni_total = 0.0

    for i, h in enumerate(clima.horas):

        # ----------------------------------------
        # timestamp
        # ----------------------------------------
        if h.timestamp is None:
            raise ValueError(f"Hora {i} sin timestamp")

        # ----------------------------------------
        # irradiancia
        # ----------------------------------------
        if h.ghi_wm2 < 0 or h.dni_wm2 < 0 or h.dhi_wm2 < 0:
            raise ValueError(f"Irradiancia negativa en hora {i}")

        # ----------------------------------------
        # temperatura (rango físico razonable)
        # ----------------------------------------
        if h.temp_amb_c < -50 or h.temp_amb_c > 80:
            raise ValueError(f"Temperatura fuera de rango en hora {i}")

        # ----------------------------------------
        # viento
        # ----------------------------------------
        if h.viento_ms < 0:
            raise ValueError(f"Viento negativo en hora {i}")

        ghi_total += h.ghi_wm2
        dni_total += h.dni_wm2

    # ----------------------------------------
    # validación global
    # ----------------------------------------
    if ghi_total <= 0:
        raise ValueError("Clima inválido: GHI total = 0")

    if dni_total <= 0:
        raise ValueError("Clima inválido: DNI total = 0")
