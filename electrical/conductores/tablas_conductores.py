from __future__ import annotations

"""
Catálogo base de conductores — FV Engine

FUENTE ÚNICA DE VERDAD para propiedades físicas.

✔ SIN dict
✔ SOLO dataclass
✔ Compatible con tramo_conductor
"""

from dataclasses import dataclass
from typing import List


# ==========================================================
# MODELO
# ==========================================================

@dataclass(frozen=True)
class Conductor:
    awg: str
    amp_a: float
    r_ohm_km: float


# ==========================================================
# TABLAS BASE
# ==========================================================

# Cobre (75°C NEC)
TABLA_BASE_CU: List[Conductor] = [
    Conductor("14", 20, 8.286),
    Conductor("12", 25, 5.211),
    Conductor("10", 35, 3.277),
    Conductor("8", 50, 2.061),
    Conductor("6", 65, 1.296),
    Conductor("4", 85, 0.815),
    Conductor("3", 100, 0.646),
    Conductor("2", 115, 0.513),
    Conductor("1", 130, 0.407),
    Conductor("1/0", 150, 0.323),
    Conductor("2/0", 175, 0.256),
    Conductor("3/0", 200, 0.203),
    Conductor("4/0", 230, 0.161),
    Conductor("250", 255, 0.128),
    Conductor("300", 285, 0.107),
    Conductor("350", 310, 0.094),
    Conductor("400", 335, 0.083),
    Conductor("500", 380, 0.066),
    Conductor("600", 420, 0.055),
    Conductor("750", 475, 0.044),
    Conductor("1000", 545, 0.033),
]


# Aluminio (75°C NEC)
TABLA_BASE_AL: List[Conductor] = [
    Conductor("12", 20, 8.487),
    Conductor("10", 30, 5.350),
    Conductor("8", 40, 3.367),
    Conductor("6", 50, 2.118),
    Conductor("4", 65, 1.335),
    Conductor("2", 90, 0.840),
    Conductor("1/0", 120, 0.528),
    Conductor("2/0", 135, 0.418),
    Conductor("3/0", 155, 0.331),
    Conductor("4/0", 180, 0.263),
    Conductor("250", 205, 0.214),
    Conductor("300", 230, 0.179),
    Conductor("350", 250, 0.158),
    Conductor("400", 270, 0.140),
    Conductor("500", 310, 0.112),
    Conductor("600", 340, 0.094),
]


# PV Wire (90°C)
TABLA_BASE_PV: List[Conductor] = [
    Conductor("14", 25, 8.286),
    Conductor("12", 30, 5.211),
    Conductor("10", 40, 3.277),
    Conductor("8", 55, 2.061),
    Conductor("6", 75, 1.296),
]


# ==========================================================
# ÍNDICES
# ==========================================================

_IDX_CU = {c.awg: c for c in TABLA_BASE_CU}
_IDX_AL = {c.awg: c for c in TABLA_BASE_AL}
_IDX_PV = {c.awg: c for c in TABLA_BASE_PV}

CALIBRES_CU = [c.awg for c in TABLA_BASE_CU]
CALIBRES_PV = [c.awg for c in TABLA_BASE_PV]


# ==========================================================
# API PÚBLICA
# ==========================================================

def calibres_cu() -> List[str]:
    return list(CALIBRES_CU)


def calibres_pv() -> List[str]:
    return list(CALIBRES_PV)


def ampacidad_cu_75c(awg: str) -> int:
    c = _IDX_CU.get(str(awg))
    return int(c.amp_a) if c else 0


def ampacidad_pv_90c(awg: str) -> int:
    c = _IDX_PV.get(str(awg))
    return int(c.amp_a) if c else 0


def resistencia_cu_ohm_km(awg: str) -> float:
    c = _IDX_CU.get(str(awg))
    return float(c.r_ohm_km) if c else 0.0


def tabla_base_conductores(material: str = "Cu") -> List[Conductor]:
    m = str(material).upper()
    return list(TABLA_BASE_AL if m == "AL" else TABLA_BASE_CU)


def tabla_base_pv() -> List[Conductor]:
    return list(TABLA_BASE_PV)


def es_calibre_valido(awg: str, *, tipo: str = "CU") -> bool:
    t = str(tipo).upper()
    lista = CALIBRES_PV if t == "PV" else CALIBRES_CU
    return str(awg) in lista


def idx_calibre(awg: str, *, tipo: str = "CU") -> int:
    t = str(tipo).upper()
    lista = CALIBRES_PV if t == "PV" else CALIBRES_CU
    return lista.index(str(awg)) if str(awg) in lista else -1
