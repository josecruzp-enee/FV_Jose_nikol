# electrical/catalogos/modelos.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PanelSpec:

    pmax_w: float

    vmp_v: float
    voc_v: float

    imp_a: float
    isc_a: float

    coef_voc_pct_c: float
    coef_vmp_pct_c: float

@dataclass(frozen=True)
class ParametrosCableado:
    vac: float = 240.0
    fases: int = 1
    fp: float = 1.0

    dist_dc_m: float = 15.0
    dist_ac_m: float = 25.0

    vdrop_obj_dc_pct: float = 2.0
    vdrop_obj_ac_pct: float = 2.0

    incluye_neutro_ac: bool = False
    otros_ccc: int = 0

    t_min_c: float = 10.0  # para Voc frío
