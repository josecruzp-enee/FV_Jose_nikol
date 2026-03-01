# core/contrato.py

from typing import TypedDict, List, Dict, Any


class ResultadoSizing(TypedDict):
    n_paneles: int
    kwp_dc: float
    pdc_kw: float
    pac_kw: float
    energia_12m: List[Dict[str, Any]]


class ResultadoStrings(TypedDict):
    ok: bool
    strings: List[Dict[str, Any]]


class ResultadoNEC(TypedDict):
    ok: bool
    paq: Dict[str, Any]


class ResultadoTecnico(TypedDict):
    sizing: ResultadoSizing
    strings: ResultadoStrings
    nec: ResultadoNEC


class ResultadoFinanciero(TypedDict):
    capex_L: float
    opex_L: float
    tir: float
    van: float
    payback_simple: float
    flujo_12m: List[Dict[str, Any]]


class ResultadoProyecto(TypedDict):
    tecnico: ResultadoTecnico
    financiero: ResultadoFinanciero
