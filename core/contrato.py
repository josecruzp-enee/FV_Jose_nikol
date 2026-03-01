# core/dto.py
from typing import TypedDict, List, Dict, Any


class ResultadoTecnico(TypedDict):
    sizing: Dict[str, Any]
    strings: Dict[str, Any]
    nec: Dict[str, Any]
    energia_12m: List[Dict[str, Any]]


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
