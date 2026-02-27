# electrical/conductores/cables_conductores.py
from __future__ import annotations

from typing import Dict, List


# ==========================================================
# Tablas (referenciales) — FUENTE ÚNICA DE VERDAD
# ==========================================================
# Nota:
# - Estas tablas son referenciales/simplificadas.
# - NEC/derating NO se aplica aquí (eso vive en factores_nec.py).
# - Este módulo solo provee catálogo base (ampacidad + resistencia) y helpers.
# - Evitamos duplicidad: NO mantenemos dicts paralelos para ampacidad/resistencia.
# - Si agregas/ajustas valores, hazlo SOLO en TABLA_BASE_*.
# ==========================================================

# Cobre (columna base referencial tipo 75°C) — incluye hasta 4/0
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

# Aluminio (columna base referencial tipo 75°C)
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

# PV Wire (columna base referencial tipo 90°C)
# Si no dimensionas PV Wire por separado, puedes eliminar este bloque y su API.
TABLA_BASE_PV: List[Dict[str, float]] = [
    {"awg": "14", "amp_a": 25, "r_ohm_km": 8.286},
    {"awg": "12", "amp_a": 30, "r_ohm_km": 5.211},
    {"awg": "10", "amp_a": 40, "r_ohm_km": 3.277},
    {"awg": "8",  "amp_a": 55, "r_ohm_km": 2.061},
    {"awg": "6",  "amp_a": 75, "r_ohm_km": 1.296},
]

# Índices para consultas O(1)
_IDX_CU: Dict[str, Dict[str, float]] = {str(r["awg"]): r for r in TABLA_BASE_CU}
_IDX_AL: Dict[str, Dict[str, float]] = {str(r["awg"]): r for r in TABLA_BASE_AL}
_IDX_PV: Dict[str, Dict[str, float]] = {str(r["awg"]): r for r in TABLA_BASE_PV}

# Listas ordenadas (delgado -> grueso), derivadas de la tabla (sin duplicidad)
CALIBRES_CU: List[str] = [str(r["awg"]) for r in TABLA_BASE_CU]
CALIBRES_PV: List[str] = [str(r["awg"]) for r in TABLA_BASE_PV]


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
    """Ampacidad base referencial Cu 75°C para un AWG."""
    return int(_IDX_CU.get(str(awg), {}).get("amp_a", 0))


def ampacidad_pv_90c(awg: str) -> int:
    """Ampacidad base referencial PV Wire 90°C para un AWG."""
    return int(_IDX_PV.get(str(awg), {}).get("amp_a", 0))


def resistencia_cu_ohm_km(awg: str) -> float:
    """Resistencia Cu referencial (ohm/km) para un AWG (Ω/km)."""
    return float(_IDX_CU.get(str(awg), {}).get("r_ohm_km", 0.0))


def tabla_base_conductores(material: str = "Cu") -> List[Dict[str, float]]:
    """
    Tabla base (ampacidad + resistencia) para Cu o Al.

    Args:
        material: 'Cu' o 'Al' (case-insensitive)
    """
    m = str(material).strip().upper()
    return list(TABLA_BASE_AL if m == "AL" else TABLA_BASE_CU)


def tabla_base_pv() -> List[Dict[str, float]]:
    """Tabla base (ampacidad + resistencia) para PV Wire (90°C)."""
    return list(TABLA_BASE_PV)


def es_calibre_valido(awg: str, *, tipo: str = "CU") -> bool:
    """
    Valida si el calibre existe en el catálogo por tipo:
      - tipo='CU' usa calibres de TABLA_BASE_CU
      - tipo='PV' usa calibres de TABLA_BASE_PV
    """
    t = str(tipo).strip().upper()
    lista = CALIBRES_PV if t == "PV" else CALIBRES_CU
    return str(awg) in lista


def idx_calibre(awg: str, *, tipo: str = "CU") -> int:
    """Índice del calibre (mayor índice = más grueso)."""
    t = str(tipo).strip().upper()
    lista = CALIBRES_PV if t == "PV" else CALIBRES_CU
    a = str(awg)
    return lista.index(a) if a in lista else -1


# ==========================================================
# Compatibilidad legacy (no romper imports antiguos)
# ==========================================================

def calibres(tipo: str = "CU") -> List[str]:
    """Compat: retorna lista de calibres por tipo legacy ('CU'|'PV')."""
    t = str(tipo).strip().upper()
    return calibres_pv() if t == "PV" else calibres_cu()


def ampacidad(awg: str, *, tipo: str = "CU") -> int:
    """Compat: ampacidad por tipo legacy ('CU'|'PV')."""
    t = str(tipo).strip().upper()
    return ampacidad_pv_90c(awg) if t == "PV" else ampacidad_cu_75c(awg)


def tabla_base(material: str = "Cu") -> List[Dict[str, float]]:
    """Compat: alias legacy de tabla_base_conductores."""
    return tabla_base_conductores(material)
