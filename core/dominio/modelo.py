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

@dataclass
class Datosproyecto:
    """
    Representa la información completa del proyecto fotovoltaico
    que será analizado por FV Engine.
    """

    # ------------------------------------------------------
    # Información general del cliente
    # ------------------------------------------------------

    cliente: str
    ubicacion: str

    # ------------------------------------------------------
    # Consumo energético
    # ------------------------------------------------------

    consumo_12m: List[float]          # consumo mensual en kWh (12 valores)

    tarifa_energia: float             # L/kWh (solo componente energía)
    cargos_fijos: float               # L/mes

    # ------------------------------------------------------
    # Producción FV
    # ------------------------------------------------------

    prod_base_kwh_kwp_mes: float      # producción base (kWh/kWp/mes)
    factores_fv_12m: List[float]      # factores mensuales (~1.0)

    cobertura_objetivo: float         # fracción del consumo a cubrir (0..1)

    # ------------------------------------------------------
    # Costos del sistema
    # ------------------------------------------------------

    costo_usd_kwp: float              # costo del sistema USD/kWp
    tcambio: float                    # tipo de cambio USD → L

    # ------------------------------------------------------
    # Financiamiento
    # ------------------------------------------------------

    tasa_anual: float                 # tasa anual del financiamiento
    plazo_anios: int                  # plazo del crédito

    porcentaje_financiado: float      # fracción financiada (0..1)

    # ------------------------------------------------------
    # Operación y mantenimiento
    # ------------------------------------------------------

    om_anual_pct: float = 0.0         # porcentaje anual del CAPEX

    # ------------------------------------------------------
    # Configuración eléctrica opcional
    # ------------------------------------------------------

    instalacion_electrica: dict | None = None
