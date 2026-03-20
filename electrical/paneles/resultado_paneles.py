from __future__ import annotations

"""
RESULTADO DEL DOMINIO PANELES — FV ENGINE
=========================================

🔷 PROPÓSITO
----------------------------------------------------------
Representar la salida del dominio paneles.

Este archivo:
    - NO calcula
    - NO transforma
    - SOLO almacena resultados ya calculados

🔷 REGLA
----------------------------------------------------------
Todas las variables aquí:
    → ya vienen calculadas desde el motor
    → son fuente de verdad para NEC y demás módulos
"""

from dataclasses import dataclass
from typing import List, Optional


# =========================================================
# STRING
# =========================================================

@dataclass(frozen=True)
class StringFV:
    """
    Representa UN string físico (detalle eléctrico).
    """

    mppt: int                  # índice del MPPT
    n_series: int              # paneles en serie

    vmp_string_v: float        # voltaje de operación
    voc_frio_string_v: float   # voltaje máximo en frío

    imp_string_a: float        # corriente de operación
    isc_string_a: float        # corriente de corto circuito

    i_mppt_a: float            # corriente hacia MPPT
    isc_mppt_a: float          # corriente máxima MPPT

    imax_pv_a: float           # corriente máxima del string
    idesign_cont_a: float      # corriente de diseño (NEC 125%)


# =========================================================
# RECOMENDACIÓN
# =========================================================

@dataclass(frozen=True)
class RecomendacionStrings:
    """
    Resultado de decisión de diseño.
    """

    n_series: int
    n_strings_total: int
    strings_por_mppt: int

    vmp_string_v: float
    vmp_stc_string_v: float
    voc_frio_string_v: float


# =========================================================
# ARRAY (🔥 SISTEMA COMPLETO DC)
# =========================================================

@dataclass(frozen=True)
class ArrayFV:
    """
    Representa el sistema completo DC.

    🔥 Fuente principal para NEC
    """

    potencia_dc_w: float       # potencia total DC

    vdc_nom: float             # voltaje nominal del sistema
    idc_nom: float             # corriente total DC (YA CALCULADA)

    isc_total: float           # corriente máxima total (YA CALCULADA)

    voc_frio_array_v: float    # voltaje máximo en frío

    n_strings_total: int
    n_paneles_total: int

    strings_por_mppt: int
    n_mppt: int

    p_panel_w: float

    # ---------------------------------------------
    # ADAPTADORES
    # ---------------------------------------------

    @property
    def pdc_kw(self) -> float:
        return self.potencia_dc_w / 1000


# =========================================================
# METADATA (SIN DICTS)
# =========================================================

@dataclass(frozen=True)
class PanelesMeta:
    """
    Información adicional del cálculo.
    """

    metodo: str
    version: Optional[str] = None
    notas: Optional[str] = None


# =========================================================
# RESULTADO FINAL
# =========================================================

@dataclass(frozen=True)
class ResultadoPaneles:
    """
    Salida oficial del dominio paneles.

    🔥 ESTE OBJETO ALIMENTA:
        - NEC
        - Energía
        - Reportes
    """

    ok: bool
    topologia: str

    array: ArrayFV
    recomendacion: RecomendacionStrings
    strings: List[StringFV]

    warnings: List[str]
    errores: List[str]

    meta: PanelesMeta
