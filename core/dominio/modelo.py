# nucleo/modelo.py

"""
CONTRATO DE ENTRADA DEL SISTEMA — FV ENGINE

Este módulo define la estructura oficial de entrada para el motor
de análisis fotovoltaico FV Engine.

Representa los datos del proyecto que serán utilizados por los
diferentes dominios del sistema:

    sizing
    paneles
    energía
    ingeniería eléctrica
    finanzas

---------------------------------------------------------------------

ARQUITECTURA

UI / API
↓
DatosProyecto
↓
core.orquestador_estudio
↓
DOMINIOS

    sizing
    paneles
    energia
    nec
    finanzas

---------------------------------------------------------------------

RESPONSABILIDAD

Definir el modelo de datos de entrada del estudio FV.

Este contrato contiene:

    • datos del cliente
    • consumo energético
    • condiciones de producción FV
    • parámetros financieros
    • configuración opcional eléctrica

---------------------------------------------------------------------

REGLAS DE ARQUITECTURA

Este módulo:

✔ define la estructura de entrada del sistema
✔ puede ser utilizado por UI, API o CLI
✔ es consumido por el orquestador del estudio

Este módulo NO debe:

✘ ejecutar cálculos
✘ acceder a bases de datos
✘ leer archivos
✘ ejecutar motores eléctricos o financieros

---------------------------------------------------------------------

VALIDACIONES ESPERADAS (EN OTROS MÓDULOS)

• consumo_12m debe contener 12 valores
• factores_fv_12m debe contener 12 valores
• cobertura_objetivo debe estar entre 0 y 1
• porcentaje_financiado debe estar entre 0 y 1

---------------------------------------------------------------------

USO

Este objeto es la entrada principal del motor:

    ejecutar_estudio(DatosProyecto)

y genera:

    ResultadoProyecto
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


# =========================================================
# DATOS DEL PROYECTO FV
# =========================================================

from dataclasses import dataclass
from typing import List

@dataclass
class Datosproyecto:

    # -------------------------------
    # Información general
    # -------------------------------
    cliente: str
    ubicacion: str

    # 🔴 FIX OBLIGATORIO
    lat: float
    lon: float

    # -------------------------------
    # Consumo
    # -------------------------------
    consumo_12m: List[float]
    tarifa_energia: float
    cargos_fijos: float

    # -------------------------------
    # Producción FV
    # -------------------------------
    prod_base_kwh_kwp_mes: float
    factores_fv_12m: List[float]
    cobertura_objetivo: float

    # -------------------------------
    # Costos
    # -------------------------------
    costo_usd_kwp: float
    tcambio: float

    # -------------------------------
    # Financiamiento
    # -------------------------------
    tasa_anual: float
    plazo_anios: int
    porcentaje_financiado: float

    # -------------------------------
    # O&M
    # -------------------------------
    om_anual_pct: float = 0.0

    # -------------------------------
    # Eléctrico opcional
    # -------------------------------
    instalacion_electrica: dict | None = None
