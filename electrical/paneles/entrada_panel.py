from dataclasses import dataclass
from typing import Optional, Literal, List

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


@dataclass(frozen=True)
class ZonaFV:
    n_paneles: int


@dataclass(frozen=True)
class EntradaPaneles:

    # ESPECIFICACIONES
    panel: PanelSpec
    inversor: InversorSpec

    # CONTROL DE FLUJO
    modo: Literal[
        "manual",
        "consumo",
        "area",
        "kw_objetivo",
        "multizona"
    ]

    # CONFIGURACIÓN BASE
    n_paneles_total: Optional[int] = None
    n_inversores: Optional[int] = None

    # 🔥 MULTIZONA (NUEVO)
    zonas: Optional[List[ZonaFV]] = None

    # OBJETIVOS
    objetivo_dc_ac: Optional[float] = None
    pdc_kw_objetivo: Optional[float] = None

    # CONDICIONES
    t_min_c: float = 25.0
    t_oper_c: float = 55.0

    # TOPOLOGÍA
    dos_aguas: bool = False
