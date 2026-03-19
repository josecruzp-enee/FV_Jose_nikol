from __future__ import annotations

"""
RESULTADO DEL DOMINIO PANELES — FV ENGINE

Este archivo es la salida oficial del dominio.
NO depende de ningún contrato externo.
"""

from dataclasses import dataclass
from typing import List, Dict, Any


# =========================================================
# STRING
# =========================================================

@dataclass(frozen=True)
class StringFV:
    mppt: int
    n_series: int
    n_strings: int

    vmp_string_v: float
    voc_frio_string_v: float

    imp_string_a: float
    isc_string_a: float

    i_mppt_a: float
    isc_mppt_a: float
    imax_pv_a: float
    idesign_cont_a: float


# =========================================================
# RECOMENDACION
# =========================================================

@dataclass(frozen=True)
class RecomendacionStrings:
    n_series: int
    n_strings_total: int
    strings_por_mppt: int

    vmp_string_v: float
    vmp_stc_string_v: float
    voc_frio_string_v: float


# =========================================================
# ARRAY
# =========================================================

@dataclass(frozen=True)
class ArrayFV:
    potencia_dc_w: float

    vdc_nom: float
    idc_nom: float

    voc_frio_array_v: float

    n_strings_total: int
    n_paneles_total: int

    strings_por_mppt: int
    n_mppt: int

    p_panel_w: float

    # =====================================================
    # ADAPTADORES (COMPATIBILIDAD CON OTROS DOMINIOS)
    # =====================================================

    @property
    def pdc_kw(self) -> float:
        """
        Compatibilidad con NEC y core.

        NEC espera pdc_kw, pero el dominio paneles
        trabaja en W.

        Conversión:
            W → kW
        """
        return self.potencia_dc_w / 1000

# =========================================================
# RESULTADO FINAL
# =========================================================

@dataclass(frozen=True)
class ResultadoPaneles:
    ok: bool
    topologia: str

    array: ArrayFV
    recomendacion: RecomendacionStrings
    strings: List[StringFV]

    warnings: List[str]
    errores: List[str]

    meta: Dict[str, Any]
