# electrical/calculos_regulacion.py
from __future__ import annotations
from typing import Dict, Optional

from electrical.conductores.tramos_base import (
    caida_tension_pct,
    elegir_calibre,
    tramo_tabla_base,
    r_cu_ohm_km,
)
def tramo_dc_ref(
    *, vmp_v: float, imp_a: float, isc_a: Optional[float], dist_m: float,
    factor_seguridad: float = 1.25, vd_obj_pct: float = 2.0
) -> Dict[str, float | str]:
    base_i = float(isc_a) if isc_a is not None else float(imp_a)
    i_diseno = float(base_i) * float(factor_seguridad)
    awg = elegir_calibre(v=vmp_v, i=imp_a, i_diseno_a=i_diseno, l_m=dist_m, vd_obj_pct=vd_obj_pct, tipo="PV", n_hilos=2)
    vd = caida_tension_pct(v=vmp_v, i=imp_a, l_m=dist_m, r_ohm_km=r_cu_ohm_km(awg), n_hilos=2)
    return {"awg": awg, "vd_pct": round(vd, 3), "vd_obj_pct": float(vd_obj_pct), "i_diseno_a": round(i_diseno, 3)}


def tramo_ac_1f_ref(
    *, vac_v: float, iac_a: float, dist_m: float,
    factor_seguridad: float = 1.25, vd_obj_pct: float = 2.0
) -> Dict[str, float | str]:
    i_diseno = float(iac_a) * float(factor_seguridad)
    awg = elegir_calibre(v=vac_v, i=iac_a, i_diseno_a=i_diseno, l_m=dist_m, vd_obj_pct=vd_obj_pct, tipo="CU", n_hilos=2)
    vd = caida_tension_pct(v=vac_v, i=iac_a, l_m=dist_m, r_ohm_km=r_cu_ohm_km(awg), n_hilos=2)
    return {"awg": awg, "vd_pct": round(vd, 3), "vd_obj_pct": float(vd_obj_pct), "i_diseno_a": round(i_diseno, 3)}


def tramo_ac_3f_ref(
    *, vll_v: float, iac_a: float, dist_m: float,
    factor_seguridad: float = 1.25, vd_obj_pct: float = 2.0
) -> Dict[str, float | str]:
    i_diseno = float(iac_a) * float(factor_seguridad)
    awg = elegir_calibre(v=vll_v, i=iac_a, i_diseno_a=i_diseno, l_m=dist_m, vd_obj_pct=vd_obj_pct, tipo="CU", n_hilos=3)
    vd = caida_tension_pct(v=vll_v, i=iac_a, l_m=dist_m, r_ohm_km=r_cu_ohm_km(awg), n_hilos=3)
    return {"awg": awg, "vd_pct": round(vd, 3), "vd_obj_pct": float(vd_obj_pct), "i_diseno_a": round(i_diseno, 3)}


# Compat reexport: se conserva nombre histórico para callers externos.
__all__ = [
    "caida_tension_pct",
    "tramo_dc_ref",
    "tramo_ac_1f_ref",
    "tramo_ac_3f_ref",
    "tramo_tabla_base",
]
