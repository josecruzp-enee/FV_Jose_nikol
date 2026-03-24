from __future__ import annotations

"""
CONTRATO MAESTRO DE RESULTADOS — FV Engine
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

from energy.resultado_energia import EnergiaResultado
from electrical.modelos.inversor import InversorSpec  # 🔥 FIX


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
    dc_ac_ratio: float 
    n_inversores: int
    paneles_por_inversor: int

    inversor: InversorSpec   # 🔥 FIX CLAVE

    energia_12m: List[MesEnergia]


# =========================================================
# INFORMACIÓN DE STRING FV
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


# =========================================================
# RESULTADO DE STRINGS
# =========================================================

@dataclass(frozen=True)
class ResultadoStrings:

    ok: bool

    n_series: int
    n_strings_total: int

    vmp_string_v: float
    voc_string_v: float

    strings: List[StringInfo]


# =========================================================
# RESULTADO NEC
# =========================================================

@dataclass(frozen=True)
class NECInversor:

    inversor: int

    idc_nom: float
    iac_nom: float


@dataclass(frozen=True)
class NECResumen:

    inversores: List[NECInversor]

    vdc_nom: float
    vac_nom: float


@dataclass(frozen=True)
class ResultadoNEC:

    ok: bool

    resumen: NECResumen

    paq: Dict[str, Any]


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


# =========================================================
# DATOS DE ENTRADA DEL PROYECTO
# =========================================================

@dataclass
class Datosproyecto:

    cliente: str
    ubicacion: str

    lat: float
    lon: float

    consumo_12m: List[float]

    tarifa_energia: float
    cargos_fijos: float

    prod_base_kwh_kwp_mes: float
    factores_fv_12m: List[float]

    cobertura_objetivo: float

    costo_usd_kwp: float
    tcambio: float

    tasa_anual: float
    plazo_anios: int

    porcentaje_financiado: float

    om_anual_pct: float = 0.0

    instalacion_electrica: dict | None = None


# =========================================================
# RESULTADO FINAL
# =========================================================

@dataclass(frozen=True)
class ResultadoProyecto:

    sizing: ResultadoSizing
    strings: ResultadoStrings
    energia: EnergiaResultado
    nec: ResultadoNEC
    financiero: ResultadoFinanciero

    ok: bool = True
    errores: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
