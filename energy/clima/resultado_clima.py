from __future__ import annotations

"""
CONTRATO DEL DOMINIO CLIMA — FV Engine
======================================

Este módulo define la SALIDA OFICIAL del dominio clima.

Responsabilidad
---------------

Representar datos climáticos horarios consistentes para
simulación fotovoltaica.

Pipeline representado:

    fuente externa (PVGIS, archivo, API)
            ↓
    normalización
            ↓
    validación
            ↓
    ResultadoClima

Este módulo NO realiza cálculos solares.
Este módulo NO calcula energía.
Este módulo NO depende de paneles.

Frontera del dominio
--------------------

Salida:
    ResultadoClima → consumido por:
        • solar (posición, POA)
        • energía

Regla arquitectónica
--------------------

    ✔ clima entrega datos físicos
    ✔ solar transforma esos datos
    ✔ energy usa resultados transformados

    ❌ clima NO conoce solar
    ❌ clima NO conoce energía
"""

from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime


# ==========================================================
# ESTADO CLIMÁTICO HORARIO
# ==========================================================

@dataclass(frozen=True)
class ClimaHora:
    """
    Representa el estado climático de una hora específica.

    Unidad base del dominio clima.
    """

    # ------------------------------------------------------
    # TIEMPO
    # ------------------------------------------------------

    timestamp: datetime
    # Fecha y hora de la medición

    # ------------------------------------------------------
    # IRRADIANCIA
    # ------------------------------------------------------

    ghi_wm2: float
    # Irradiancia global horizontal

    dni_wm2: float
    # Irradiancia directa normal

    dhi_wm2: float
    # Irradiancia difusa horizontal

    # ------------------------------------------------------
    # CONDICIONES AMBIENTALES
    # ------------------------------------------------------

    temp_amb_c: float
    # Temperatura ambiente

    viento_ms: float
    # Velocidad del viento


# ==========================================================
# RESULTADO COMPLETO DEL DOMINIO CLIMA
# ==========================================================

@dataclass(frozen=True)
class ResultadoClima:
    """
    Resultado completo del dominio clima.

    Contiene una serie horaria validada de 8760 registros.
    """

    # ------------------------------------------------------
    # UBICACIÓN
    # ------------------------------------------------------

    latitud: float
    longitud: float

    # ------------------------------------------------------
    # SERIE HORARIA
    # ------------------------------------------------------

    horas: List[ClimaHora]
    # Debe contener exactamente 8760 registros

    # ------------------------------------------------------
    # TRAZABILIDAD
    # ------------------------------------------------------

    fuente: str = "desconocido"
    # Origen de los datos (PVGIS, archivo, etc.)

    meta: Dict[str, object] = field(default_factory=dict)
    # Información adicional del dataset


# ==========================================================
# VALIDACIÓN DEL DOMINIO
# ==========================================================

def validar_clima_8760(clima: ResultadoClima) -> None:
    """
    Valida consistencia física y estructural del clima.

    Reglas:

        • Debe contener exactamente 8760 horas
        • No se permiten valores negativos de irradiancia
        • Temperaturas dentro de rango físico
        • Viento no negativo
        • GHI total debe ser > 0

    Lanza:
        ValueError si el clima es inválido
    """

    # ------------------------------------------------------
    # VALIDACIÓN ESTRUCTURAL
    # ------------------------------------------------------

    if not clima.horas:
        raise ValueError("ResultadoClima no contiene horas")

    if len(clima.horas) != 8760:
        raise ValueError(
            f"Se esperaban 8760 horas, pero hay {len(clima.horas)}"
        )

    # ------------------------------------------------------
    # ACUMULADORES
    # ------------------------------------------------------

    ghi_total = 0.0
    dni_total = 0.0

    # ------------------------------------------------------
    # VALIDACIÓN POR HORA
    # ------------------------------------------------------

    for i, h in enumerate(clima.horas):

        # -------------------------------
        # timestamp
        # -------------------------------
        if h.timestamp is None:
            raise ValueError(f"Hora {i} sin timestamp")

        # -------------------------------
        # irradiancia
        # -------------------------------
        if h.ghi_wm2 < 0 or h.dni_wm2 < 0 or h.dhi_wm2 < 0:
            raise ValueError(f"Irradiancia negativa en hora {i}")

        # -------------------------------
        # consistencia básica
        # -------------------------------
        if h.ghi_wm2 < h.dhi_wm2:
            print(f"⚠️ GHI < DHI en hora {i} (posible inconsistencia)")

        # -------------------------------
        # temperatura
        # -------------------------------
        if h.temp_amb_c < -50 or h.temp_amb_c > 80:
            raise ValueError(f"Temperatura fuera de rango en hora {i}")

        # -------------------------------
        # viento
        # -------------------------------
        if h.viento_ms < 0:
            raise ValueError(f"Viento negativo en hora {i}")

        ghi_total += h.ghi_wm2
        dni_total += h.dni_wm2

    # ------------------------------------------------------
    # VALIDACIÓN GLOBAL
    # ------------------------------------------------------

    if ghi_total <= 0:
        raise ValueError("Clima inválido: GHI total = 0")

    if dni_total == 0:
        print("⚠️ DNI = 0 → se usará modelo difuso (válido en PVGIS)")


# ==========================================================
# ESTRUCTURA DEL DOMINIO
# ==========================================================

"""
Este módulo produce:

ResultadoClima


Estructura:

ResultadoClima
    ├─ latitud
    ├─ longitud
    │
    ├─ horas (8760)
    │      ├─ timestamp
    │      ├─ ghi_wm2
    │      ├─ dni_wm2
    │      ├─ dhi_wm2
    │      ├─ temp_amb_c
    │      └─ viento_ms
    │
    ├─ fuente
    └─ meta


Flujo de integración:

PVGIS / API / archivo
        ↓
lector_clima
        ↓
normalizador_clima
        ↓
ResultadoClima
        ↓
solar (POA)
        ↓
energy


Fronteras:

✔ clima → datos físicos
✔ solar → geometría e irradiancia
✔ energy → potencia y energía

Este módulo NO cruza esas fronteras.
"""
