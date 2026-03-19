from __future__ import annotations
from dataclasses import dataclass
from typing import List


# ==========================================================
# STRING
# ==========================================================

@dataclass(frozen=True)
class StringFV:
    id: int
    inversor: int
    mppt: int

    n_series: int

    vmp_string_v: float
    voc_string_v: float

    imp_string_a: float
    isc_string_a: float


# ==========================================================
# ARRAY FV
# ==========================================================

@dataclass(frozen=True)
class ArrayFV:
    pdc_kw: float
    n_strings: int


# ==========================================================
# RESULTADO PANELes
# ==========================================================

@dataclass(frozen=True)
class ResultadoPaneles:
    ok: bool

    array: ArrayFV
    strings: List[StringFV]
