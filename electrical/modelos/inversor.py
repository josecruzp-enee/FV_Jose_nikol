# electrical/catalogos/modelos.py
from __future__ import annotations
from dataclasses import dataclass


from dataclasses import dataclass


@dataclass(frozen=True)
class InversorSpec:

    kw_ac: float

    n_mppt: int

    mppt_min_v: float
    mppt_max_v: float

    vdc_max_v: float

    imppt_max_a: float | None = None


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
