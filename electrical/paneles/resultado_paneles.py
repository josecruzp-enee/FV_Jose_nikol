from __future__ import annotations

"""
RESULTADO DEL DOMINIO PANELES

Fuente única de verdad del generador FV.
"""

from dataclasses import dataclass
from typing import List


# =========================================================
# STRING (SIN NEC)
# =========================================================

@dataclass(frozen=True)
class StringFV:
    mppt: int
    n_series: int

    vmp_string_v: float
    voc_frio_string_v: float

    imp_string_a: float
    isc_string_a: float


# =========================================================
# RECOMENDACIÓN
# =========================================================

@dataclass(frozen=True)
class RecomendacionStrings:
    n_series: int
    n_strings_total: int
    strings_por_mppt: int

    vmp_string_v: float
    voc_frio_string_v: float


# =========================================================
# ARRAY FV
# =========================================================

@dataclass(frozen=True)
class ArrayFV:
    potencia_dc_w: float

    vdc_nom: float
    idc_nom: float
    isc_total: float

    voc_frio_array_v: float

    n_strings_total: int
    n_paneles_total: int

    strings_por_mppt: int
    n_mppt: int

    p_panel_w: float

    @property
    def pdc_kw(self) -> float:
        return self.potencia_dc_w / 1000


# =========================================================
# META
# =========================================================

@dataclass(frozen=True)
class PanelesMeta:
    n_paneles_total: int
    pdc_kw: float
    n_inversores: int


# =========================================================
# RESULTADO FINAL
# =========================================================

from electrical.modelos.paneles import PanelSpec  # 👈 IMPORTANTE

@dataclass(frozen=True)
class ResultadoPaneles:
    ok: bool
    topologia: str

    panel: PanelSpec   # 🔥 ESTA LÍNEA NUEVA

    array: ArrayFV
    recomendacion: RecomendacionStrings
    strings: List[StringFV]

    warnings: List[str]
    errores: List[str]

    meta: PanelesMeta
