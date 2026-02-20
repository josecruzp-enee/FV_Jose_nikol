# electrical/cables_conductores.py
from __future__ import annotations

from typing import Dict, List

# ==========================================================
# Tablas (referenciales)
# ==========================================================

# Ampacidad Cu 75°C (simplificada, referencial)
AMPACIDAD_CU_75C: Dict[str, int] = {
    "14": 20, "12": 25, "10": 35, "8": 50, "6": 65,
    "4": 85, "3": 100, "2": 115, "1": 130, "1/0": 150,
}

# Ampacidad PV Wire 90°C (simplificada, referencial)
AMPACIDAD_PV_90C: Dict[str, int] = {"14": 25, "12": 30, "10": 40, "8": 55, "6": 75}

# Resistencia Cu (ohm/km) referencial
RESISTENCIA_CU_OHM_KM: Dict[str, float] = {
    "14": 8.286, "12": 5.211, "10": 3.277, "8": 2.061, "6": 1.296,
    "4": 0.815, "3": 0.647, "2": 0.513, "1": 0.407, "1/0": 0.323,
}

# Orden de calibres (delgado -> grueso)
CALIBRES_CU: List[str] = ["14", "12", "10", "8", "6", "4", "3", "2", "1", "1/0"]
CALIBRES_PV: List[str] = ["14", "12", "10", "8", "6"]


# ==========================================================
# Tablas base para cálculos NEC (referenciales)
# (ampacidad base + resistencia). Ajustes NEC se hacen en otro módulo.
# ==========================================================

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
]

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
]


# ==========================================================
# Funciones públicas (consulta / referencia)
# ==========================================================

def calibres_cu() -> List[str]:
    """Lista ordenada de calibres Cu (delgado -> grueso)."""
    return list(CALIBRES_CU)


def calibres_pv() -> List[str]:
    """Lista ordenada de calibres PV Wire (delgado -> grueso)."""
    return list(CALIBRES_PV)


def ampacidad_cu_75c(awg: str) -> int:
    """Ampacidad referencial Cu 75°C para un AWG."""
    return int(AMPACIDAD_CU_75C.get(str(awg), 0))


def ampacidad_pv_90c(awg: str) -> int:
    """Ampacidad referencial PV Wire 90°C para un AWG."""
    return int(AMPACIDAD_PV_90C.get(str(awg), 0))


def resistencia_cu_ohm_km(awg: str) -> float:
    """Resistencia Cu referencial (ohm/km) para un AWG."""
    return float(RESISTENCIA_CU_OHM_KM.get(str(awg), 0.0))


def tabla_base_conductores(material: str = "Cu") -> List[Dict[str, float]]:
    """Tabla base (ampacidad + resistencia) para Cu o Al."""
    m = str(material).strip().upper()
    return list(TABLA_BASE_AL if m == "AL" else TABLA_BASE_CU)


def es_calibre_valido(awg: str, *, tipo: str = "CU") -> bool:
    """Valida si el calibre existe en el catálogo (CU o PV)."""
    t = str(tipo).strip().upper()
    lista = CALIBRES_PV if t == "PV" else CALIBRES_CU
    return str(awg) in lista


def idx_calibre(awg: str, *, tipo: str = "CU") -> int:
    """Índice del calibre (mayor índice = más grueso)."""
    t = str(tipo).strip().upper()
    lista = CALIBRES_PV if t == "PV" else CALIBRES_CU
    return lista.index(str(awg)) if str(awg) in lista else -1
