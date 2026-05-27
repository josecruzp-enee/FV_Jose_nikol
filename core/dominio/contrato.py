from __future__ import annotations

"""
CONTRATOS DEL SISTEMA FV ENGINE
Solo DTOs (dataclasses).
SIN lógica.
"""

from dataclasses import dataclass, field
from typing import List, Any, Optional


# ==========================================================
# ENERGÍA
# ==========================================================

@dataclass(frozen=True)
class MesEnergia:
    mes: str
    consumo_kwh: float
    generacion_kwh: float
    energia_red_kwh: float


# ==========================================================
# SIZING
# ==========================================================

@dataclass(frozen=True)
class ResultadoSizing:

    n_paneles: int
    kwp_dc: float
    pdc_kw: float

    kw_ac: float
    kw_ac_total: float

    n_inversores: int
    paneles_por_inversor: int

    inversor: Any
    panel: Any

    dc_ac_ratio: float
    energia_12m: List[MesEnergia]

    ok: bool = True
    errores: List[str] = field(default_factory=list)


# ==========================================================
# LAYOUT PRELIMINAR FV
# ==========================================================

@dataclass(frozen=True)
class ResultadoLayoutPreliminar:
    n_paneles: int

    area_panel_m2: float
    area_bruta_m2: float
    factor_ocupacion: float
    area_necesaria_m2: float

    filas: int
    columnas: int
    paneles_colocados: int
    paneles_sobrantes: int

    ancho_total_m: float
    largo_total_m: float
    area_rectangular_m2: float

    largo_panel_m: float
    ancho_panel_m: float
    separacion_x_m: float
    separacion_y_m: float

    nota: str = (
        "Layout preliminar informativo. No considera obstáculos, sombras, "
        "orientación real ni verificación estructural."
    )


# ==========================================================
# FINANZAS
# ==========================================================

@dataclass(frozen=True)
class ResultadoFinanciero:
    ok: bool
    errores: List[str]

    capex_L: float
    tir: float
    van: float
    payback_simple: float


# ==========================================================
# RESULTADO FINAL
# ==========================================================

@dataclass
class ResultadoProyecto:
    sizing: Optional[ResultadoSizing]
    paneles: Any
    strings: Any
    energia: Any
    electrical: Any
    financiero: Optional[ResultadoFinanciero]

    layout_preliminar: Optional[ResultadoLayoutPreliminar] = None
    optimizacion_economica: Any = None

    ok: bool = True
    errores: List[str] = field(default_factory=list)
