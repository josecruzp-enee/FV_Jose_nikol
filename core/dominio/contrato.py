from dataclasses import dataclass
from typing import List, Dict, Any
from electrical.energia.contrato import EnergiaResultado

# =============================
# Energía mensual
# =============================

@dataclass(frozen=True)
class MesEnergia:
    mes: str
    consumo_kwh: float
    generacion_kwh: float
    energia_red_kwh: float


# =============================
# Sizing
# =============================

@dataclass
class ResultadoSizing:
    n_paneles: int
    kwp_dc: float
    pdc_kw: float
    pac_kw: float
    n_inversores: int
    energia_12m: List[MesEnergia]


# =============================
# Strings
# =============================

@dataclass(frozen=True)
class StringInfo:
    mppt: int
    n_series: int
    n_paralelo: int
    vmp_string_v: float
    voc_frio_string_v: float
    imp_a: float
    isc_a: float


@dataclass(frozen=True)
class ResultadoStrings:
    ok: bool
    strings: List[StringInfo]


# =============================
# NEC
# =============================

@dataclass(frozen=True)
class NECResumen:
    idc_nom: float
    iac_nom: float
    vdc_nom: float
    vac_nom: float


@dataclass(frozen=True)
class ResultadoNEC:
    ok: bool
    resumen: NECResumen
    paq: Dict[str, Any]


# =============================
# Finanzas
# =============================

@dataclass(frozen=True)
class ResultadoFinanciero:
    capex_L: float
    opex_L: float
    tir: float
    van: float
    payback_simple: float
    flujo_12m: List[Dict[str, float]]


# =============================
# Proyecto final
# =============================

# =============================
# Proyecto final
# =============================

@dataclass(frozen=True)
class ResultadoProyecto:
    sizing: ResultadoSizing
    strings: ResultadoStrings
    energia: EnergiaResultado
    nec: ResultadoNEC
    financiero: ResultadoFinanciero
