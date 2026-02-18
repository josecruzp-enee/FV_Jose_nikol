# electrical/modelos.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Panel:
    nombre: str
    w: float
    vmp: float
    voc: float
    imp: float
    isc: float
    tc_voc_frac_c: float = -0.0029  # -0.29%/°C típico

@dataclass(frozen=True)
class Inversor:
    nombre: str
    kw_ac: float
    n_mppt: int
    vmppt_min: float
    vmppt_max: float
    vdc_max: float
    imppt_max: float = 25.0  # A por MPPT (referencial)

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
