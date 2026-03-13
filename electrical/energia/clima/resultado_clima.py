from __future__ import annotations

"""
CONTRATO DEL DOMINIO CLIMA — FV Engine

Este módulo define las estructuras oficiales de datos
climáticos utilizadas por el motor energético del sistema.

Regla arquitectónica
--------------------
Este archivo representa la frontera del dominio clima.

Ningún módulo externo debe depender de implementaciones
internas como:

    lector_pvgis
    clima_tmy
    generador_clima_base

Todos los módulos consumidores deben utilizar únicamente
las estructuras definidas aquí.

Consumidores típicos
--------------------

    simulacion_8760
    orquestador_energia
"""


from dataclasses import dataclass
from typing import List


# ==========================================================
# DATOS CLIMÁTICOS POR HORA
# ==========================================================

@dataclass(frozen=True)
class ClimaHora:
    """
    Datos climáticos de una hora específica.
    """

    # Irradiancia global horizontal
    ghi_wm2: float

    # Temperatura ambiente
    temp_amb_c: float


# ==========================================================
# RESULTADO CLIMÁTICO ANUAL
# ==========================================================

@dataclass(frozen=True)
class ResultadoClima:
    """
    Serie climática anual utilizada por el simulador 8760.

    Contiene 8760 registros horarios.
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
