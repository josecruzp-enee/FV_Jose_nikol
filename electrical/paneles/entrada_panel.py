from __future__ import annotations

"""
CONTRATO DE ENTRADA — DOMINIO PANELES

Define el problema eléctrico FV.
NO calcula. NO transforma.
"""

from dataclasses import dataclass
from typing import Optional

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


@dataclass(frozen=True)
class EntradaPaneles:
    """
    Problema eléctrico del sistema FV.
    """

    # ESPECIFICACIONES
    panel: PanelSpec
    inversor: InversorSpec

    # CONFIGURACIÓN
    n_paneles_total: Optional[int] = None
    n_inversores: Optional[int] = None

    # CONDICIONES
    t_min_c: float = 25.0
    t_oper_c: float = 55.0

    # TOPOLOGÍA
    dos_aguas: bool = False

    # OBJETIVO
    objetivo_dc_ac: Optional[float] = None
    pdc_kw_objetivo: Optional[float] = None
