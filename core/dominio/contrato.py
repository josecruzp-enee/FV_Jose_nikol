from __future__ import annotations

"""
CONTRATOS DEL SISTEMA FV ENGINE
Solo DTOs (dataclasses).
SIN lógica.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


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

    # ==================================================
    # CAMPOS OBLIGATORIOS
    # ==================================================
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

    # ==================================================
    # CAMPOS CON DEFAULT (SIEMPRE AL FINAL)
    # ==================================================
    ok: bool = True
    errores: List[str] = field(default_factory=list)

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

    ok: bool = True
    errores: List[str] = field(default_factory=list)
