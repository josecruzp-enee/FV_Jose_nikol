# electrical/cableado.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
import math

from electrical.modelos import ParametrosCableado

# Ampacidad CU 75°C (simplificada)
AMP_CU_75C = {"14":20,"12":25,"10":35,"8":50,"6":65,"4":85,"3":100,"2":115,"1":130,"1/0":150}
# PV wire referencial
AMP_PV_90C = {"14":25,"12":30,"10":40,"8":55,"6":75}
# R ohm/km Cu
R_OHM_KM_CU = {"14":8.286,"12":5.211,"10":3.277,"8":2.061,"6":1.296,"4":0.815,"3":0.647,"2":0.513,"1":0.407,"1/0":0.323}

GAUGES_CU = ["14","12","10","8","6","4","3","2","1","1/0"]
GAUGES_PV = ["14","12","10","8","6"]


def _vdrop_pct_2wire(V: float, I: float, L_m: float, gauge: str) -> float:
    R_m = (R_OHM_KM_CU[gauge] / 1000.0)
    vdrop = 2.0 * I * R_m * L_m
    return (vdrop / V) * 100.0


def _pick_by_ampacity(table: dict, I: float, gauges: List[str]) -> str:
    for g in gauges:
        if table.get(g, 0) >= I:
            return g
    return gauges[-1]


def _pick_by_vdrop(V: float, I: float, L_m: float, target_pct: float, gauges: List[str]) -> str:
    for g in gauges:
        if _vdrop_pct_2wire(V, I, L_m, g) <= target_pct:
            return g
    return gauges[-1]


def _max_gauge(g1: str, g2: str, gauges: List[str]) -> str:
    return g1 if gauges.index(g1) > gauges.index(g2) else g2


def _breaker_sugerido(i_continua: float) -> int:
    # escalones típicos
    for b in [30, 40, 50, 60, 70, 80, 90, 100]:
        if i_continua <= b:
            return b
    return 125


def _conduit_heuristico(ac_gauge: str, incluye_neutro: bool, extra_ccc: int) -> str:
    ccc = 2 + (1 if incluye_neutro else 0) + max(0, int(extra_ccc))
    if ac_gauge in ["14","12","10","8"]:
        base = '1/2"'
    elif ac_gauge == "6":
        base = '3/4"'
    else:
        base = '1"'
    if ccc >= 4:
        if base == '1/2"': return '3/4"'
        if base == '3/4"': return '1"'
        return '1-1/4"'
    return base


def calcular_cableado_referencial(
    *,
    params: ParametrosCableado,
    vmp_string_v: float,
    imp_a: float,
    isc_a: Optional[float],
    iac_estimado_a: float,
) -> Dict[str, Any]:
    """
    Retorna dict con recomendaciones DC/AC:
      - calibre por ampacidad y por caída (elige el mayor)
      - caída resultante
      - breaker y tubería sugerida (heurística)
      - texto_pdf: lista bullets
      - disclaimer
    """
    # AC: carga continua
    i_ac_diseno = 1.25 * float(iac_estimado_a)

    g_amp_ac = _pick_by_ampacity(AMP_CU_75C, i_ac_diseno, GAUGES_CU)
    g_vd_ac = _pick_by_vdrop(params.vac, float(iac_estimado_a), params.dist_ac_m, params.vdrop_obj_ac_pct, GAUGES_CU)
    g_ac = _max_gauge(g_amp_ac, g_vd_ac, GAUGES_CU)
    vd_ac = _vdrop_pct_2wire(params.vac, float(iac_estimado_a), params.dist_ac_m, g_ac)

    breaker = _breaker_sugerido(i_ac_diseno)
    conduit = _conduit_heuristico(g_ac, params.incluye_neutro_ac, params.otros_ccc)
    tierra = "10" if GAUGES_CU.index(g_ac) >= GAUGES_CU.index("6") else "12"

    # DC: si hay Isc, usa Isc*1.25; si no, Imp*1.25
    i_dc = 1.25 * (float(isc_a) if isc_a is not None else float(imp_a))

    g_amp_dc = _pick_by_ampacity(AMP_PV_90C, i_dc, GAUGES_PV)
    g_vd_dc = _pick_by_vdrop(vmp_string_v, float(imp_a), params.dist_dc_m, params.vdrop_obj_dc_pct, GAUGES_PV)
    g_dc = _max_gauge(g_amp_dc, g_vd_dc, GAUGES_PV)
    vd_dc = _vdrop_pct_2wire(vmp_string_v, float(imp_a), params.dist_dc_m, g_dc)

    texto_pdf = [
        f"Conductores DC (string): {g_dc} AWG Cu PV Wire/USE-2 (UV). Dist {params.dist_dc_m:.1f} m | caída {vd_dc:.2f}% (obj {params.vdrop_obj_dc_pct:.1f}%).",
        f"Conductores AC (salida inversor): {g_ac} AWG Cu THHN/THWN-2 (L1+L2)"
        + (" + N" if params.incluye_neutro_ac else "")
        + f" + tierra {tierra} AWG. Dist {params.dist_ac_m:.1f} m | caída {vd_ac:.2f}% (obj {params.vdrop_obj_ac_pct:.1f}%).",
        f"Tubería AC sugerida: {conduit} EMT/PVC (según cantidad de conductores y facilidad de jalado).",
        f"Breaker AC sugerido (referencial): {breaker} A (validar contra datasheet del inversor).",
    ]

    disclaimer = (
        "Cálculo referencial para propuesta. Calibre final sujeto a: temperatura, agrupamiento (CCC), "
        "factor de ajuste/corrección, fill real de tubería, terminales 75°C y normativa local/NEC aplicable."
    )

    return {
        "ac": {"gauge_awg": g_ac, "vdrop_pct": round(vd_ac, 2), "breaker_a": breaker, "conduit": conduit, "tierra_awg": tierra},
        "dc": {"gauge_awg": g_dc, "vdrop_pct": round(vd_dc, 2)},
        "texto_pdf": texto_pdf,
        "disclaimer": disclaimer,
    }
