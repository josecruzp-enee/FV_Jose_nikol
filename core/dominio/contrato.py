from __future__ import annotations

"""
CONTRATO MAESTRO — FV ENGINE

Define:
- Entrada del sistema (Datosproyecto)
- Resultados de cada módulo
- Resultado final del pipeline

Reglas:
- Entrada fuerte (dataclass)
- Datos internos flexibles (dict controlado)
- Sin duplicaciones
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
# RESULTADO STRINGS (PANELES)
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
# ENTRADA DEL SISTEMA (🔥 CLAVE)
# =========================================================

@dataclass
class Datosproyecto:

    # -------------------------------
    # Información general
    # -------------------------------
    cliente: str
    ubicacion: str

    lat: float
    lon: float

    # -------------------------------
    # Consumo
    # -------------------------------
    consumo_12m: List[float]

    tarifa_energia: float
    cargos_fijos: float

    # -------------------------------
    # Producción FV
    # -------------------------------
    prod_base_kwh_kwp_mes: List[float]
    factores_fv_12m: List[float]

    cobertura_objetivo: float

    # -------------------------------
    # Costos
    # -------------------------------
    costo_usd_kwp: float
    tcambio: float

    # -------------------------------
    # Financiamiento
    # -------------------------------
    tasa_anual: float
    plazo_anios: int
    porcentaje_financiado: float

    # -------------------------------
    # O&M
    # -------------------------------
    om_anual_pct: float = 0.0

    # =====================================================
    # 🔥 CAMPOS CRÍTICOS DEL PIPELINE
    # =====================================================

    # FV (modo, valor, zonas, etc.)
    sistema_fv: Dict[str, Any] = field(default_factory=dict)

    # Equipos (panel_id, inversor_id, etc.)
    equipos: Dict[str, Any] = field(default_factory=dict)

    # Eléctrico (vac, fases, distancias, etc.)
    electrico: Dict[str, Any] = field(default_factory=dict)


# =========================================================
# RESULTADO FINAL DEL SISTEMA
# =========================================================

@dataclass
class ResultadoProyecto:

    # ==================================================
    # RESULTADOS PRINCIPALES
    # ==================================================
    sizing: ResultadoSizing | None
    strings: Any
    energia: Any
    electrical: Any
    financiero: ResultadoFinanciero | None

    # ==================================================
    # ESTADO Y DEBUG
    # ==================================================
    ok: bool = True
    errores: List[str] = field(default_factory=list)

    trazas: Dict[str, str] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
