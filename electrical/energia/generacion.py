from typing import Dict, Any, List
from .hsp import hsp_honduras_conservador_12m
from .orientacion import factor_orientacion_total

DIAS_MES: List[int] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def normalizar_sistema_fv(sf: Dict[str, Any]) -> Dict[str, Any]:
    sf = dict(sf)

    hsp = sf.get("hsp")
    if hsp is None:
        hsp = float(sf.get("hsp_kwh_m2_d", 5.2))

    sf["hsp"] = float(hsp)
    sf["hsp_kwh_m2_d"] = float(sf["hsp"])

    label = str(sf.get("tipo_superficie", "")).strip()

    sf["tipo_superficie_code"] = (
        "dos_aguas" if label == "Techo dos aguas" else "plano"
    )

    return sf


def preview_generacion_anual(sf: Dict[str, Any]) -> Dict[str, Any]:

    sf = normalizar_sistema_fv(sf)

    kwp = float(sf.get("kwp_preview", 5.0))
    perd = float(sf.get("perdidas_sistema_pct", 15.0))
    sombras = float(sf.get("sombras_pct", 0.0))

    pr = (1.0 - perd / 100.0) * (1.0 - sombras / 100.0)
    pr = max(0.10, min(1.00, pr))

    if bool(sf.get("hsp_override", False)):
        hsp_12m = [float(sf.get("hsp_kwh_m2_d", 5.2))] * 12
    else:
        hsp_12m = hsp_honduras_conservador_12m()

    f_orient = factor_orientacion_total(
        tipo_superficie=sf.get("tipo_superficie_code"),
        azimut_deg=sf.get("azimut_deg", 180),
        azimut_a_deg=sf.get("azimut_a_deg"),
        azimut_b_deg=sf.get("azimut_b_deg"),
        reparto_pct_a=sf.get("reparto_pct_a"),
        hemisferio="norte",
    )

    gen_mes = [
        kwp * h * pr * f_orient * d
        for h, d in zip(hsp_12m, DIAS_MES)
    ]

    gen_dia = [
        (g / d) if d else 0.0
        for g, d in zip(gen_mes, DIAS_MES)
    ]

    return {
        "gen_mes": gen_mes,
        "gen_dia_prom": gen_dia,
        "total_kwh_anual": sum(gen_mes),
        "pr": pr,
        "factor_orientacion": f_orient,
        "hsp_12m": hsp_12m,
    }
