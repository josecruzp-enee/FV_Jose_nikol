from __future__ import annotations

"""
RESULTADO DEL DOMINIO PANELES — FV ENGINE

Representa la salida final del dominio paneles.

REGLA:
- NO calcula
- NO transforma
- SOLO almacena resultados ya calculados
"""

from dataclasses import dataclass
from typing import List


# =========================================================
# STRING (DETALLE)
# =========================================================

@dataclass(frozen=True)
class StringFV:
    """
    Representa un string físico del sistema FV.
    """

    mppt: int
    n_series: int

    vmp_string_v: float
    voc_frio_string_v: float

    imp_string_a: float
    isc_string_a: float

    i_mppt_a: float
    isc_mppt_a: float

    imax_pv_a: float
    idesign_cont_a: float


# =========================================================
# RECOMENDACIÓN
# =========================================================

@dataclass(frozen=True)
class RecomendacionStrings:
    """
    Resultado de decisión de diseño del sistema.
    """

    n_series: int
    n_strings_total: int
    strings_por_mppt: int

    vmp_string_v: float
    vmp_stc_string_v: float
    voc_frio_string_v: float


# =========================================================
# ARRAY (SISTEMA COMPLETO DC)
# =========================================================

@dataclass(frozen=True)
class ArrayFV:
    """
    Representa el sistema completo DC.

    Fuente principal para NEC y cálculos eléctricos posteriores.
    """

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

    # ---------------------------------------------
    # ADAPTADORES
    # ---------------------------------------------

    @property
    def pdc_kw(self) -> float:
        return self.potencia_dc_w / 1000

    @property
    def n_strings(self) -> int:
        return self.n_strings_total


# =========================================================
# META (SIN DICTS)
# =========================================================

@dataclass(frozen=True)
class PanelesMeta:
    """
    Datos auxiliares del cálculo.
    """

    n_paneles_total: int
    pdc_kw: float
    n_inversores: int


# =========================================================
# RESULTADO FINAL
# =========================================================

@dataclass(frozen=True)
class ResultadoPaneles:
    """
    Salida oficial del dominio paneles.

    ESTE OBJETO ALIMENTA:
        - Corrientes
        - NEC
        - Conductores
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


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# OBJETO PRINCIPAL:
# ----------------------------------------------------------
# ResultadoPaneles
#
#
# ----------------------------------------------------------
# ENTRADA (IMPLÍCITA)
# ----------------------------------------------------------
#
# Este archivo NO recibe entrada directa.
#
# Es construido por:
#   electrical.paneles.orquestador_paneles
#
#
# ----------------------------------------------------------
# PROCESO (ORIGEN DE DATOS)
# ----------------------------------------------------------
#
# Los datos provienen de:
#
#   1. dimensionar_paneles
#       → número de paneles
#       → potencia DC
#
#   2. calcular_strings_fv
#       → configuración eléctrica
#       → voltajes
#       → corrientes
#
#   3. distribución MPPT
#
#
# ----------------------------------------------------------
# VARIABLES CLAVE
# ----------------------------------------------------------
#
# ArrayFV:
#
#   potencia_dc_w
#       → potencia total del sistema
#
#   vdc_nom
#       → voltaje del generador FV
#
#   idc_nom
#       → corriente DC de operación
#
#   isc_total
#       → corriente máxima del sistema
#
#   voc_frio_array_v
#       → voltaje máximo en frío
#
#   n_strings_total
#       → número total de strings
#
#   n_paneles_total
#       → número total de módulos
#
#
# ----------------------------------------------------------
# DETALLE DEL SISTEMA
# ----------------------------------------------------------
#
# strings: List[StringFV]
#
# Cada string contiene:
#   - configuración eléctrica
#   - voltajes
#   - corrientes
#
#
# ----------------------------------------------------------
# RECOMENDACIÓN
# ----------------------------------------------------------
#
# recomendacion: RecomendacionStrings
#
# Define:
#   - módulos en serie
#   - número de strings
#   - voltajes
#
#
# ----------------------------------------------------------
# SALIDA
# ----------------------------------------------------------
#
# ResultadoPaneles:
#
#   ok
#   topologia
#   array
#   recomendacion
#   strings
#   warnings
#   errores
#   meta
#
#
# ----------------------------------------------------------
# UBICACIÓN
# ----------------------------------------------------------
#
# electrical/paneles/
#
#
# ----------------------------------------------------------
# FLUJO GLOBAL
# ----------------------------------------------------------
#
# EntradaPaneles
#       ↓
# ejecutar_paneles
#       ↓
# ResultadoPaneles  ← ESTE ARCHIVO
#       ↓
# Corrientes
#       ↓
# Conductores
#       ↓
# NEC
#
#
# ----------------------------------------------------------
# PRINCIPIO
# ----------------------------------------------------------
#
# Este objeto es la fuente única de verdad del sistema FV.
#
# Ningún módulo debe recalcular estos valores.
#
# ==========================================================
