"""
Catálogo base de conductores — FV Engine

FRONTERA DEL MÓDULO
-------------------

Este módulo provee la base de datos de conductores utilizada
por el dominio `conductores`.

Contiene únicamente:

    - ampacidad base
    - resistencia del conductor
    - lista de calibres disponibles

NO aplica:

    - factores NEC
    - correcciones de temperatura
    - correcciones por CCC
    - cálculo de caída de voltaje

Es la FUENTE ÚNICA DE VERDAD para datos físicos del conductor.
"""

from __future__ import annotations
from typing import Dict, List


# ==========================================================
# TABLAS BASE
# ==========================================================

# Cobre (75°C referencia NEC)
TABLA_BASE_CU: List[Dict[str, float]] = [
    {"awg": "14",  "amp_a": 20,  "r_ohm_km": 8.286},
    {"awg": "12",  "amp_a": 25,  "r_ohm_km": 5.211},
    {"awg": "10",  "amp_a": 35,  "r_ohm_km": 3.277},
    {"awg": "8",   "amp_a": 50,  "r_ohm_km": 2.061},
    {"awg": "6",   "amp_a": 65,  "r_ohm_km": 1.296},
    {"awg": "4",   "amp_a": 85,  "r_ohm_km": 0.815},
    {"awg": "3",   "amp_a": 100, "r_ohm_km": 0.646},
    {"awg": "2",   "amp_a": 115, "r_ohm_km": 0.513},
    {"awg": "1",   "amp_a": 130, "r_ohm_km": 0.407},
    {"awg": "1/0", "amp_a": 150, "r_ohm_km": 0.323},
    {"awg": "2/0", "amp_a": 175, "r_ohm_km": 0.256},
    {"awg": "3/0", "amp_a": 200, "r_ohm_km": 0.203},
    {"awg": "4/0", "amp_a": 230, "r_ohm_km": 0.161},

    {"awg": "250", "amp_a": 255, "r_ohm_km": 0.128},
    {"awg": "300", "amp_a": 285, "r_ohm_km": 0.107},
    {"awg": "350", "amp_a": 310, "r_ohm_km": 0.094},
    {"awg": "400", "amp_a": 335, "r_ohm_km": 0.083},
    {"awg": "500", "amp_a": 380, "r_ohm_km": 0.066},
    {"awg": "600", "amp_a": 420, "r_ohm_km": 0.055},
    {"awg": "750", "amp_a": 475, "r_ohm_km": 0.044},
    {"awg": "1000", "amp_a": 545, "r_ohm_km": 0.033},
]


# Aluminio (75°C referencia)
TABLA_BASE_AL: List[Dict[str, float]] = [
    {"awg": "12",  "amp_a": 20,  "r_ohm_km": 8.487},
    {"awg": "10",  "amp_a": 30,  "r_ohm_km": 5.350},
    {"awg": "8",   "amp_a": 40,  "r_ohm_km": 3.367},
    {"awg": "6",   "amp_a": 50,  "r_ohm_km": 2.118},
    {"awg": "4",   "amp_a": 65,  "r_ohm_km": 1.335},
    {"awg": "2",   "amp_a": 90,  "r_ohm_km": 0.840},
    {"awg": "1/0", "amp_a": 120, "r_ohm_km": 0.528},
    {"awg": "2/0", "amp_a": 135, "r_ohm_km": 0.418},
    {"awg": "3/0", "amp_a": 155, "r_ohm_km": 0.331},
    {"awg": "4/0", "amp_a": 180, "r_ohm_km": 0.263},

    {"awg": "250", "amp_a": 205, "r_ohm_km": 0.214},
    {"awg": "300", "amp_a": 230, "r_ohm_km": 0.179},
    {"awg": "350", "amp_a": 250, "r_ohm_km": 0.158},
    {"awg": "400", "amp_a": 270, "r_ohm_km": 0.140},
    {"awg": "500", "amp_a": 310, "r_ohm_km": 0.112},
    {"awg": "600", "amp_a": 340, "r_ohm_km": 0.094},
]


# PV Wire (90°C)
TABLA_BASE_PV: List[Dict[str, float]] = [
    {"awg": "14", "amp_a": 25, "r_ohm_km": 8.286},
    {"awg": "12", "amp_a": 30, "r_ohm_km": 5.211},
    {"awg": "10", "amp_a": 40, "r_ohm_km": 3.277},
    {"awg": "8",  "amp_a": 55, "r_ohm_km": 2.061},
    {"awg": "6",  "amp_a": 75, "r_ohm_km": 1.296},
]


# ==========================================================
# ÍNDICES
# ==========================================================

_IDX_CU = {str(r["awg"]): r for r in TABLA_BASE_CU}
_IDX_AL = {str(r["awg"]): r for r in TABLA_BASE_AL}
_IDX_PV = {str(r["awg"]): r for r in TABLA_BASE_PV}

CALIBRES_CU = [str(r["awg"]) for r in TABLA_BASE_CU]
CALIBRES_PV = [str(r["awg"]) for r in TABLA_BASE_PV]


# ==========================================================
# API PÚBLICA
# ==========================================================

def calibres_cu() -> List[str]:
    return list(CALIBRES_CU)


def calibres_pv() -> List[str]:
    return list(CALIBRES_PV)


def ampacidad_cu_75c(awg: str) -> int:
    return int(_IDX_CU.get(str(awg), {}).get("amp_a", 0))


def ampacidad_pv_90c(awg: str) -> int:
    return int(_IDX_PV.get(str(awg), {}).get("amp_a", 0))


def resistencia_cu_ohm_km(awg: str) -> float:
    return float(_IDX_CU.get(str(awg), {}).get("r_ohm_km", 0.0))


def tabla_base_conductores(material: str = "Cu") -> List[Dict[str, float]]:
    m = str(material).upper()
    return list(TABLA_BASE_AL if m == "AL" else TABLA_BASE_CU)


def tabla_base_pv() -> List[Dict[str, float]]:
    return list(TABLA_BASE_PV)


def es_calibre_valido(awg: str, *, tipo: str = "CU") -> bool:
    t = str(tipo).upper()
    lista = CALIBRES_PV if t == "PV" else CALIBRES_CU
    return str(awg) in lista


def idx_calibre(awg: str, *, tipo: str = "CU") -> int:
    t = str(tipo).upper()
    lista = CALIBRES_PV if t == "PV" else CALIBRES_CU
    return lista.index(str(awg)) if str(awg) in lista else -1
