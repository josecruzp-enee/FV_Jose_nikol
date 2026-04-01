from __future__ import annotations

"""
CONTRATO MAESTRO — FV ENGINE

Define:
- Resultados de cada módulo
- Resultado final del pipeline

Reglas:
- Entrada NO vive aquí
- Solo outputs del sistema
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


# =========================================================
# ENERGÍA MENSUAL
# =========================================================

@dataclass(frozen=True)
class MesEnergia:
    mes: str
    consumo_kwh: float
    generacion_kwh: float
    energia_red_kwh: float


# =========================================================
# RESULTADO DEL SIZING
# =========================================================

@dataclass(frozen=True)
class ResultadoSizing:

    n_paneles: int
    kwp_dc: float
    pdc_kw: float

    kw_ac: float
    kw_ac_total: float

    dc_ac_ratio: float

    n_inversores: int
    paneles_por_inversor: int

    inversor: Any
    panel: Any

    energia_12m: List[MesEnergia]

    sugerencias: List[Dict[str, Any]] = field(default_factory=list)

    ok: bool = True
    errores: List[str] = field(default_factory=list)


# =========================================================
# RESULTADO STRINGS
# =========================================================

@dataclass(frozen=True)
class StringInfo:

    id: int
    inversor: int
    mppt: int

    n_series: int

    vmp_string_v: float
    voc_frio_string_v: float

    imp_string_a: float
    isc_string_a: float


@dataclass(frozen=True)
class ResultadoStrings:

    ok: bool

    n_series: int
    n_strings_total: int

    vmp_string_v: float
    voc_string_v: float

    strings: List[StringInfo]

    errores: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# =========================================================
# RESULTADO FINANCIERO
# =========================================================

@dataclass(frozen=True)
class ResultadoFinanciero:

    capex_L: float
    opex_L: float

    tir: float
    van: float
    payback_simple: float

    flujo_12m: List[Dict[str, float]]

    ok: bool = True
    errores: List[str] = field(default_factory=list)


# =========================================================
# RESULTADO FINAL
# =========================================================

@dataclass
class ResultadoProyecto:

    sizing: ResultadoSizing | None
    strings: Any
    energia: Any
    electrical: Any
    financiero: ResultadoFinanciero | None

    ok: bool = True
    errores: List[str] = field(default_factory=list)

    trazas: Dict[str, str] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
