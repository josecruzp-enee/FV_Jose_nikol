"""
CONTRATO MAESTRO DE RESULTADOS — FV ENGINE

Este módulo define las estructuras oficiales de salida del motor FV Engine.
No contiene lógica de cálculo. Solo define modelos de datos utilizados
para transportar resultados entre dominios del sistema.

---------------------------------------------------------------------

ARQUITECTURA

UI
↓
core.orquestador_estudio
↓
DOMINIOS

    paneles
    energia
    ingenieria_electrica (NEC)
    finanzas

↓
ResultadoProyecto

---------------------------------------------------------------------

RESPONSABILIDAD

Definir los contratos de datos que representan los resultados generados
por cada dominio del sistema FV:

    ResultadoSizing
    ResultadoStrings
    ResultadoNEC
    ResultadoFinanciero
    ResultadoProyecto

Estos modelos permiten transportar datos entre capas sin acoplar
los dominios entre sí.

---------------------------------------------------------------------

REGLAS DE ARQUITECTURA

Este módulo:

✔ define estructuras de datos del dominio
✔ es consumido por core, UI y reportes

Este módulo NO debe:

✘ ejecutar cálculos
✘ leer archivos
✘ ejecutar simulaciones
✘ depender de UI o PDF
✘ contener lógica de negocio

---------------------------------------------------------------------

FLUJO DEL SISTEMA

DatosProyecto
↓
Sizing
↓
Strings
↓
Energía
↓
Ingeniería NEC
↓
Finanzas
↓
ResultadoProyecto
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from electrical.energia.contrato import EnergiaResultado


# =========================================================
# ENERGÍA MENSUAL
# =========================================================

@dataclass(frozen=True)
class MesEnergia:
    """
    Representa el balance energético mensual del sistema FV.
    """

    mes: str
    consumo_kwh: float
    generacion_kwh: float
    energia_red_kwh: float


# =========================================================
# RESULTADO DEL SIZING
# =========================================================

@dataclass
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

    energia_12m: List[MesEnergia]


# =========================================================
# INFORMACIÓN DE STRINGS FV
# =========================================================

@dataclass(frozen=True)
class StringInfo:
    """
    Información eléctrica de un string conectado a un MPPT.
    """

    inversor: int
    mppt: int

    n_series: int
    n_paralelo: int

    vmp_string_v: float
    voc_frio_string_v: float

    imp_a: float
    isc_a: float


@dataclass(frozen=True)
class ResultadoStrings:
    """
    Resultado del cálculo de configuración de strings FV.
    """

    ok: bool
    strings: List[StringInfo]


# =========================================================
# RESULTADO NEC
# =========================================================

@dataclass(frozen=True)
class NECInversor:
    """
    Corrientes nominales del inversor utilizadas en ingeniería NEC.
    """

    inversor: int
    idc_nom: float
    iac_nom: float


@dataclass(frozen=True)
class NECResumen:
    """
    Resumen eléctrico del sistema utilizado por la ingeniería NEC.
    """

    inversores: List[NECInversor]
    vdc_nom: float
    vac_nom: float


@dataclass(frozen=True)
class ResultadoNEC:
    """
    Resultado del cálculo de ingeniería eléctrica NEC.
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
    Resultado del análisis financiero del sistema FV.
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

@dataclass(frozen=True)
class ResultadoProyecto:
    """
    Resultado final consolidado del estudio FV.

    Este contrato unifica los resultados generados por
    todos los dominios del motor FV Engine.
    """

    sizing: ResultadoSizing
    strings: ResultadoStrings
    energia: EnergiaResultado
    nec: ResultadoNEC
    financiero: ResultadoFinanciero
