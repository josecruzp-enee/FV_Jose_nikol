from typing import TypedDict, List, Dict, Any
class MesEnergia(TypedDict):
    mes: str
    consumo_kwh: float
    generacion_kwh: float
    energia_red_kwh: float


class ResultadoSizing(TypedDict):
    n_paneles: int
    kwp_dc: float
    pdc_kw: float
    pac_kw: float
    energia_12m: List[MesEnergia]


class StringInfo(TypedDict):
    mppt: int
    n_series: int
    n_paralelo: int
    vmp_string_v: float
    voc_frio_string_v: float
    imp_a: float
    isc_a: float


class ResultadoStrings(TypedDict):
    ok: bool
    strings: List[StringInfo]


class NECResumen(TypedDict):
    idc_nom: float
    iac_nom: float
    vdc_nom: float
    vac_nom: float


class ResultadoNEC(TypedDict):
    ok: bool
    resumen: NECResumen
    paq: Dict[str, Any]  # si necesitas detalle bruto


class ResultadoFinanciero(TypedDict):
    capex_L: float
    opex_L: float
    tir: float
    van: float
    payback_simple: float
    flujo_12m: List[Dict[str, float]]

class ResultadoTecnico(TypedDict):
    sizing: ResultadoSizing
    strings: ResultadoStrings
    nec: ResultadoNEC


class ResultadoProyecto(TypedDict):
    tecnico: ResultadoTecnico
    financiero: ResultadoFinanciero
