from __future__ import annotations

"""
CONTRATO DE ENTRADA DEL SISTEMA — FV ENGINE (ALINEADO)

Este modelo representa la entrada oficial del sistema FV.

PIPELINE REAL:

    sizing
    paneles
    energia
    electrical   ✅ (reemplaza NEC)
    finanzas

Este módulo define SOLO datos.
NO contiene lógica.
"""

from dataclasses import dataclass
from typing import List
from dataclasses import dataclass

# ==========================================================
# EQUIPOS (FV)
# ==========================================================
@dataclass
class Equipos:
    panel_id: str
    inversor_id: str

# =========================================================
# MODELO ELÉCTRICO (TIPADO FUERTE)
# =========================================================

@dataclass
class InstalacionElectrica:
    """
    Parámetros eléctricos del sistema.
    """

    vac: float                 # Voltaje línea o monofásico
    fases: int = 1             # 1 o 3
    fp: float = 1.0            # Factor de potencia

    dist_dc_m: float = 0.0     # Distancia DC
    dist_ac_m: float = 0.0     # Distancia AC


# =========================================================
# DATOS DEL PROYECTO FV
# =========================================================

@dataclass
class Datosproyecto:

    # -------------------------------
    # Información general
    # -------------------------------
    cliente: str
    ubicacion: str

    lat: float
    lon: float

    # -------------------------------
    # Consumo
    # -------------------------------
    consumo_12m: List[float]          # 12 valores
    tarifa_energia: float
    cargos_fijos: float

    # -------------------------------
    # Producción FV
    # -------------------------------
    prod_base_kwh_kwp_mes: float
    factores_fv_12m: List[float]      # 12 factores
    cobertura_objetivo: float         # 0–1

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
    porcentaje_financiado: float      # 0–1

    # -------------------------------
    # O&M
    # -------------------------------
    om_anual_pct: float = 0.0

    # -------------------------------
    # Eléctrico
    # -------------------------------
    instalacion_electrica: InstalacionElectrica | None = None
