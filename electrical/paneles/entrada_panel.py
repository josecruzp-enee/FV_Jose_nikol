"""
Entrada del dominio paneles.

Normaliza payload proveniente de UI/API y construye el objeto
EntradaPaneles que será consumido por el orquestador del dominio.

Este módulo NO realiza cálculos eléctricos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


# =========================
# Contrato de entrada
# =========================

@dataclass
class EntradaPaneles:

    panel: Any
    inversor: Any

    n_paneles_total: Optional[int]

    t_min_c: float
    t_oper_c: Optional[float]

    dos_aguas: bool

    objetivo_dc_ac: Optional[float]
    pdc_kw_objetivo: Optional[float]


# =========================
# Helpers de normalización
# =========================

def _f(x: Any, default: float = 0.0) -> float:
    """Convierte cualquier valor a float seguro."""
    try:
        return float(x)
    except Exception:
        return float(default)


def _i(x: Any, default: int = 0) -> int:
    """Convierte cualquier valor a entero seguro."""
    try:
        return int(x)
    except Exception:
        return int(default)


def _clamp(x: float, lo: float, hi: float) -> float:
    """Limita un valor float a un rango."""
    return max(lo, min(hi, float(x)))


# =========================
# Constructor de entrada
# =========================

def build_entrada_paneles(
    *,
    panel: Any,
    inversor: Any,
    n_paneles_total: Optional[int] = None,
    t_min_c: float,
    dos_aguas: bool,
    objetivo_dc_ac: Optional[float] = 1.2,
    pdc_kw_objetivo: Optional[float] = None,
    t_oper_c: Optional[float] = 55.0,
) -> EntradaPaneles:
    """
    Construye EntradaPaneles normalizando inputs provenientes de UI/API.
    """

    n_total = _i(n_paneles_total, 0) if n_paneles_total is not None else None

    # Temperatura mínima ambiente
    tmin = _clamp(_f(t_min_c, 0.0), -40.0, 40.0)

    # Temperatura de operación módulo
    toper = _f(t_oper_c, 55.0) if t_oper_c is not None else None
    if toper is not None:
        toper = _clamp(toper, 25.0, 85.0)

    # Objetivo DC/AC
    odc = _f(objetivo_dc_ac, 1.2) if objetivo_dc_ac is not None else None
    if odc is not None:
        odc = _clamp(odc, 0.8, 1.6)

    # Potencia objetivo DC
    pdc_obj = _f(pdc_kw_objetivo, 0.0) if pdc_kw_objetivo is not None else None
    if pdc_obj is not None and pdc_obj <= 0:
        pdc_obj = None

    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        n_paneles_total=n_total,
        t_min_c=tmin,
        t_oper_c=toper,
        dos_aguas=bool(dos_aguas),
        objetivo_dc_ac=odc,
        pdc_kw_objetivo=pdc_obj,
    )
