# nucleo/electrico_ref.py
from __future__ import annotations

from typing import Any, Dict, List, Optional


AMP_CU_75C = {
    "14": 20, "12": 25, "10": 35, "8": 50, "6": 65, "4": 85, "3": 100,
    "2": 115, "1": 130, "1/0": 150,
}

AMP_PV_90C = {"14": 25, "12": 30, "10": 40, "8": 55, "6": 75}

R_OHM_KM_CU = {
    "14": 8.286, "12": 5.211, "10": 3.277, "8": 2.061, "6": 1.296,
    "4": 0.815, "3": 0.647, "2": 0.513, "1": 0.407, "1/0": 0.323,
}

GAUGES_CU = ["14","12","10","8","6","4","3","2","1","1/0"]
GAUGES_PV = ["14","12","10","8","6"]


def _vdrop_pct_1ph_2wire(V: float, I: float, L_m: float, gauge: str) -> float:
    R_km = R_OHM_KM_CU[gauge]
    R_m = R_km / 1000.0
    vdrop = 2.0 * I * R_m * L_m
    return (vdrop / V) * 100.0


def _pick_gauge_by_ampacity(table: Dict[str, float], I_design: float, gauges: List[str]) -> str:
    for g in gauges:
        if table.get(g, 0) >= I_design:
            return g
    return gauges[-1]


def _pick_gauge_by_vdrop(V: float, I: float, L_m: float, target_pct: float, gauges: List[str]) -> str:
    for g in gauges:
        pct = _vdrop_pct_1ph_2wire(V, I, L_m, g)
        if pct <= target_pct:
            return g
    return gauges[-1]


def _max_gauge(g1: str, g2: str, gauges: List[str]) -> str:
    i1, i2 = gauges.index(g1), gauges.index(g2)
    return g1 if i1 > i2 else g2


def _recomendar_conduit(ac_gauge: str, incluye_neutro: bool, extra_ccc: int = 0) -> str:
    ccc = 2 + (1 if incluye_neutro else 0) + max(0, extra_ccc)
    if ac_gauge in ["14","12","10","8"]:
        base = "1/2\""
    elif ac_gauge == "6":
        base = "3/4\""
    else:
        base = "1\""

    if ccc >= 4:
        if base == "1/2\"":
            return "3/4\""
        if base == "3/4\"":
            return "1\""
        return "1-1/4\""
    return base


def simular_electrico_fv_para_pdf(
    *,
    v_ac: float = 240.0,
    i_ac_estimado: float = 41.7,
    dist_ac_m: float = 25.0,
    objetivo_vdrop_ac_pct: float = 2.0,
    vmp_string_v: float = 410.0,
    imp_a: float = 13.2,
    isc_a: Optional[float] = None,
    dist_dc_m: float = 15.0,
    objetivo_vdrop_dc_pct: float = 2.0,
    incluye_neutro_ac: bool = False,
    otros_ccc_en_misma_tuberia: int = 0,
) -> Dict[str, Any]:

    i_ac_diseno = 1.25 * i_ac_estimado
    if isc_a is not None:
        i_dc_max = 1.25 * isc_a
    else:
        i_dc_max = 1.25 * imp_a

    g_amp_ac = _pick_gauge_by_ampacity(AMP_CU_75C, i_ac_diseno, GAUGES_CU)
    g_vd_ac  = _pick_gauge_by_vdrop(v_ac, i_ac_estimado, dist_ac_m, objetivo_vdrop_ac_pct, GAUGES_CU)
    g_final_ac = _max_gauge(g_amp_ac, g_vd_ac, GAUGES_CU)
    vdrop_ac_pct = _vdrop_pct_1ph_2wire(v_ac, i_ac_estimado, dist_ac_m, g_final_ac)

    conduit_ac = _recomendar_conduit(g_final_ac, incluye_neutro_ac, otros_ccc_en_misma_tuberia)
    egc = "10" if GAUGES_CU.index(g_final_ac) >= GAUGES_CU.index("6") else "12"

    if i_ac_diseno <= 50:
        breaker_a = 50
    elif i_ac_diseno <= 60:
        breaker_a = 60
    elif i_ac_diseno <= 70:
        breaker_a = 70
    else:
        breaker_a = 80

    g_amp_dc = _pick_gauge_by_ampacity(AMP_PV_90C, i_dc_max, GAUGES_PV)
    g_vd_dc  = _pick_gauge_by_vdrop(vmp_string_v, imp_a, dist_dc_m, objetivo_vdrop_dc_pct, GAUGES_PV)
    g_final_dc = _max_gauge(g_amp_dc, g_vd_dc, GAUGES_PV)
    vdrop_dc_pct = _vdrop_pct_1ph_2wire(vmp_string_v, imp_a, dist_dc_m, g_final_dc)
    conduit_dc = "1/2\"" if g_final_dc in ["14","12","10"] else "3/4\""

    retur
