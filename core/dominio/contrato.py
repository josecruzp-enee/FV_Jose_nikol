from __future__ import annotations

"""
CONTRATO MAESTRO DE RESULTADOS — FV Engine

Este archivo define todas las estructuras de datos que representan
los resultados del motor FV.

Reglas de arquitectura:

- Ningún módulo externo debe depender de estructuras internas
  de cálculo de los dominios.

- Todos los módulos consumidores deben usar exclusivamente
  las clases definidas aquí.

Este contrato unifica los resultados de:

    sizing
    paneles / strings
    ingeniería eléctrica
    energía
    finanzas
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

from energy.resultado_energia import EnergiaResultado
from electrical.modelos.inversor import InversorSpec


# =========================================================
# ENERGÍA MENSUAL
# =========================================================

@dataclass(frozen=True)
class MesEnergia:
    """
    Balance energético mensual del sistema FV.
    """

    mes: str
    consumo_kwh: float
    generacion_kwh: float
    energia_red_kwh: float


# =========================================================
# RESULTADO DEL SIZING
# =========================================================




@dataclass(frozen=True)
class ResultadoSizing:
    """
    Resultado del dimensionamiento del sistema FV.
    """

    n_paneles: int

    kwp_dc: float
    pdc_kw: float

    kw_ac: float

    n_inversores: int
    paneles_por_inversor: int

    inversor: InversorSpec   # 🔥 FIX CLAVE

    energia_12m: List[MesEnergia]

# =========================================================
# INFORMACIÓN DE STRING FV
# =========================================================

@dataclass(frozen=True)
class StringInfo:
    """
    Representa un string conectado a un MPPT.
    """

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
    """
    Resultado del cálculo de configuración del generador FV.
    """

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
    """
    Corrientes nominales por inversor para ingeniería NEC.
    """

    inversor: int

    idc_nom: float
    iac_nom: float


@dataclass(frozen=True)
class NECResumen:
    """
    Resumen eléctrico del sistema FV.
    """

    inversores: List[NECInversor]

    vdc_nom: float
    vac_nom: float


@dataclass(frozen=True)
class ResultadoNEC:
    """
    Resultado del cálculo de ingeniería eléctrica.
    """

    ok: bool

    resumen: NECResumen

    paq: Dict[str, Any]


# =========================================================
# RESULTADO FINANCIERO
# =========================================================

@dataclass(frozen=True)
class ResultadoFinanciero:
    """
    Resultado del análisis financiero del proyecto FV.
    """

    capex_L: float
    opex_L: float

    tir: float
    van: float
    payback_simple: float

    flujo_12m: List[Dict[str, float]]


# =========================================================
# RESULTADO FINAL DEL PROYECTO
# =========================================================
@dataclass
class Datosproyecto:

    # ------------------------------------------------------
    # Información general del cliente
    # ------------------------------------------------------

    cliente: str
    ubicacion: str

    # 🔴 NUEVO — UBICACIÓN GEOGRÁFICA (OBLIGATORIO)
    lat: float
    lon: float

    # ------------------------------------------------------
    # Consumo energético
    # ------------------------------------------------------

    consumo_12m: List[float]

    tarifa_energia: float
    cargos_fijos: float

    # ------------------------------------------------------
    # Producción FV
    # ------------------------------------------------------

    prod_base_kwh_kwp_mes: float
    factores_fv_12m: List[float]

    cobertura_objetivo: float

    # ------------------------------------------------------
    # Costos del sistema
    # ------------------------------------------------------

    costo_usd_kwp: float
    tcambio: float

    # ------------------------------------------------------
    # Financiamiento
    # ------------------------------------------------------

    tasa_anual: float
    plazo_anios: int

    porcentaje_financiado: float

    # ------------------------------------------------------
    # O&M
    # ------------------------------------------------------

    om_anual_pct: float = 0.0

    # ------------------------------------------------------
    # Configuración eléctrica opcional
    # ------------------------------------------------------

    instalacion_electrica: dict | None = None

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
