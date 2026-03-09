"""
Contrato del dominio PANELes (generador FV DC).

Define la salida oficial del módulo paneles.
Otros módulos (corrientes, protecciones, NEC, UI, PDF)
solo deben consumir este contrato.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any


# =========================================================
# Información eléctrica por string / MPPT
# =========================================================

@dataclass
class StringFV:
    mppt: int
    n_series: int
    n_strings: int

    vmp_string_v: float
    voc_frio_string_v: float

    i_mppt_a: float

    # valores útiles para NEC
    isc_array_a: float
    imax_pv_a: float
    idesign_cont_a: float


# =========================================================
# Recomendación del motor
# =========================================================

@dataclass
class RecomendacionStrings:

    n_series: int
    n_strings_total: int
    strings_por_mppt: int

    vmp_string_v: float
    vmp_stc_string_v: float
    voc_frio_string_v: float


# =========================================================
# SALIDA OFICIAL DEL DOMINIO
# =========================================================

@dataclass
class ResultadoPaneles:

    ok: bool

    # configuración FV
    topologia: str

    recomendacion: RecomendacionStrings

    # detalle por MPPT / string
    strings: List[StringFV]

    # estado del cálculo
    warnings: List[str]
    errores: List[str]

    # información auxiliar / trazabilidad
    meta: Dict[str, Any]
