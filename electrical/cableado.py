# electrical/cableado.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import math

from electrical.modelos import ParametrosCableado


# ==========================================================
# Tablas (referenciales)
# ==========================================================

# Ampacidad CU 75°C (simplificada)
AMP_CU_75C = {"14": 20, "12": 25, "10": 35, "8": 50, "6": 65, "4": 85, "3": 100, "2": 115, "1": 130, "1/0": 150}

# PV wire referencial
AMP_PV_90C = {"14": 25, "12": 30, "10": 40, "8": 55, "6": 75}

# R ohm/km Cu
R_OHM_KM_CU = {"14": 8.286, "12": 5.211, "10": 3.277, "8": 2.061, "6": 1.296, "4": 0.815, "3": 0.647, "2": 0.513, "1": 0.407, "1/0": 0.323}

GAUGES_CU = ["14", "12", "10", "8", "6", "4", "3", "2", "1", "1/0"]
GAUGES_PV = ["14", "12", "10", "8", "6"]


# ==========================================================
# Utils pequeños
# ==========================================================

def _cfg_get(cfg_tecnicos: Optional[Dict[str, Any]], key: str, default: float) -> float:
    if not cfg_tecnicos:
        return float(default)
    try:
        return float(cfg_tecnicos.get(key, default))
    except Exception:
        return float(default)


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
    # el "mayor" es el de índice más alto en la lista (más grueso)
    return g1 if gauges.index(g1) > gauges.index(g2) else g2


def _breaker_sugerido(i_continua: float) -> int:
    for b in [30, 40, 50, 60, 70, 80, 90, 100]:
        if i_continua <= b:
            return b
    return 125


def _conduit_heuristico(ac_gauge: str, incluye_neutro: bool, extra_ccc: int) -> str:
    ccc = 2 + (1 if incluye_neutro else 0) + max(0, int(extra_ccc))

    if ac_gauge in ["14", "12", "10", "8"]:
        base = '1/2"'
    elif ac_gauge == "6":
        base = '3/4"'
    else:
        base = '1"'

    if ccc >= 4:
        if base == '1/2"':
            return '3/4"'
        if base == '3/4"':
            return '1"'
        return '1-1/4"'

    return base


# ==========================================================
# Subcálculos (funciones cortas)
# ==========================================================

def _calcular_ac(
    *,
    params: ParametrosCableado,
    iac_estimado_a: float,
    cfg_tecnicos: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Selección AC:
      - I diseño = iac_estimado * factor_seguridad_ac (default 1.25)
      - gauge por ampacidad y por vdrop (elige el mayor)
      - retorna gauge, vdrop, breaker, conduit, tierra
    """
    f_ac = _cfg_get(cfg_tecnicos, "factor_seguridad_ac", 1.25)
    vdrop_obj_ac = _cfg_get(cfg_tecnicos, "vdrop_obj_ac_pct", float(getattr(params, "vdrop_obj_ac_pct", 2.0)))

    i_ac_diseno = float(iac_estimado_a) * float(f_ac)

    g_amp = _pick_by_ampacity(AMP_CU_75C, i_ac_diseno, GAUGES_CU)
    g_vd = _pick_by_vdrop(float(params.vac), float(iac_estimado_a), float(params.dist_ac_m), float(vdrop_obj_ac), GAUGES_CU)
    g_ac = _max_gauge(g_amp, g_vd, GAUGES_CU)

    vd_ac = _vdrop_pct_2wire(float(params.vac), float(iac_estimado_a), float(params.dist_ac_m), g_ac)

    breaker = _breaker_sugerido(i_ac_diseno)
    conduit = _conduit_heuristico(g_ac, bool(params.incluye_neutro_ac), int(params.otros_ccc))
    tierra = "10" if GAUGES_CU.index(g_ac) >= GAUGES_CU.index("6") else "12"

    return {
        "gauge_awg": g_ac,
        "vdrop_pct": round(vd_ac, 2),
        "breaker_a": int(breaker),
        "conduit": str(conduit),
        "tierra_awg": str(tierra),
        "vdrop_obj_pct": float(vdrop_obj_ac),
        "i_diseno_a": float(i_ac_diseno),
        "factor_seguridad": float(f_ac),
    }


def _calcular_dc(
    *,
    params: ParametrosCableado,
    vmp_string_v: float,
    imp_a: float,
    isc_a: Optional[float],
    cfg_tecnicos: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Selección DC:
      - I diseño = (Isc o Imp) * factor_seguridad_dc (default 1.25)
      - gauge por ampacidad y por vdrop (elige el mayor)
      - retorna gauge, vdrop
    """
    f_dc = _cfg_get(cfg_tecnicos, "factor_seguridad_dc", 1.25)
    vdrop_obj_dc = _cfg_get(cfg_tecnicos, "vdrop_obj_dc_pct", float(getattr(params, "vdrop_obj_dc_pct", 2.0)))

    base_i = float(isc_a) if isc_a is not None else float(imp_a)
    i_dc_diseno = float(base_i) * float(f_dc)

    g_amp = _pick_by_ampacity(AMP_PV_90C, i_dc_diseno, GAUGES_PV)
    g_vd = _pick_by_vdrop(float(vmp_string_v), float(imp_a), float(params.dist_dc_m), float(vdrop_obj_dc), GAUGES_PV)
    g_dc = _max_gauge(g_amp, g_vd, GAUGES_PV)

    vd_dc = _vdrop_pct_2wire(float(vmp_string_v), float(imp_a), float(params.dist_dc_m), g_dc)

    return {
        "gauge_awg": g_dc,
        "vdrop_pct": round(vd_dc, 2),
        "vdrop_obj_pct": float(vdrop_obj_dc),
        "i_diseno_a": float(i_dc_diseno),
        "factor_seguridad": float(f_dc),
    }


def _texto_pdf(
    *,
    params: ParametrosCableado,
    ac: Dict[str, Any],
    dc: Dict[str, Any],
) -> List[str]:
    ac_line = (
        f"Conductores AC (salida inversor): {ac['gauge_awg']} AWG Cu THHN/THWN-2 (L1+L2)"
        + (" + N" if params.incluye_neutro_ac else "")
        + f" + tierra {ac['tierra_awg']} AWG. Dist {params.dist_ac_m:.1f} m | caída {ac['vdrop_pct']:.2f}% "
          f"(obj {ac['vdrop_obj_pct']:.1f}%)."
    )

    dc_line = (
        f"Conductores DC (string): {dc['gauge_awg']} AWG Cu PV Wire/USE-2 (UV). Dist {params.dist_dc_m:.1f} m | "
        f"caída {dc['vdrop_pct']:.2f}% (obj {dc['vdrop_obj_pct']:.1f}%)."
    )

    return [
        dc_line,
        ac_line,
        f"Tubería AC sugerida: {ac['conduit']} EMT/PVC (según cantidad de conductores y facilidad de jalado).",
        f"Breaker AC sugerido (referencial): {ac['breaker_a']} A (validar contra datasheet del inversor).",
    ]


def _disclaimer() -> str:
    return (
        "Cálculo referencial para propuesta. Calibre final sujeto a: temperatura, agrupamiento (CCC), "
        "factor de ajuste/corrección, fill real de tubería, terminales 75°C y normativa local/NEC aplicable."
    )


# ==========================================================
# API pública
# ==========================================================

def calcular_cableado_referencial(
    *,
    params: ParametrosCableado,
    vmp_string_v: float,
    imp_a: float,
    isc_a: Optional[float],
    iac_estimado_a: float,
    cfg_tecnicos: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Retorna dict con recomendaciones DC/AC:
      - calibre por ampacidad y por caída (elige el mayor)
      - caída resultante
      - breaker y tubería sugerida (heurística)
      - texto_pdf: lista bullets
      - disclaimer

    cfg_tecnicos (opcional):
      - vdrop_obj_dc_pct, vdrop_obj_ac_pct
      - factor_seguridad_dc, factor_seguridad_ac
    """
    ac = _calcular_ac(params=params, iac_estimado_a=iac_estimado_a, cfg_tecnicos=cfg_tecnicos)
    dc = _calcular_dc(params=params, vmp_string_v=vmp_string_v, imp_a=imp_a, isc_a=isc_a, cfg_tecnicos=cfg_tecnicos)

    texto_pdf = _texto_pdf(params=params, ac=ac, dc=dc)

    return {
        "ac": {
            "gauge_awg": ac["gauge_awg"],
            "vdrop_pct": ac["vdrop_pct"],
            "breaker_a": ac["breaker_a"],
            "conduit": ac["conduit"],
            "tierra_awg": ac["tierra_awg"],
            "i_diseno_a": ac["i_diseno_a"],
            "vdrop_obj_pct": ac["vdrop_obj_pct"],
        },
        "dc": {
            "gauge_awg": dc["gauge_awg"],
            "vdrop_pct": dc["vdrop_pct"],
            "i_diseno_a": dc["i_diseno_a"],
            "vdrop_obj_pct": dc["vdrop_obj_pct"],
        },
        "texto_pdf": texto_pdf,
        "disclaimer": _disclaimer(),
    }
