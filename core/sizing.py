# nucleo/sizing.py
from __future__ import annotations

import math
from typing import Any, Dict, Optional

from .modelo import modelo
from .simulacion_12m import capex_L, consumo_anual, consumo_promedio


INVERSORES_COMERCIALES = [1, 2, 3, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50]


def seleccionar_inversor_kw(valor_kw: float) -> float:
    for kw in INVERSORES_COMERCIALES:
        if kw >= valor_kw:
            return float(kw)
    return float(INVERSORES_COMERCIALES[-1])


def _validar_entrada_dimensionamiento(
    kwh_mes: float,
    cobertura_obj: float,
    hsp: float,
    pr: float,
    dias_mes: float,
    panel_wp: int,
    dc_ac_ratio: float,
    area_panel_m2: float
) -> None:
    if kwh_mes <= 0:
        raise ValueError("kwh_mes debe ser > 0")
    if not (0.0 < cobertura_obj <= 1.0):
        raise ValueError("cobertura_obj debe estar entre 0 y 1")
    if hsp <= 0:
        raise ValueError("hsp debe ser > 0")
    if not (0.0 < pr <= 1.0):
        raise ValueError("pr debe estar entre 0 y 1")
    if dias_mes <= 0:
        raise ValueError("dias_mes debe ser > 0")
    if panel_wp <= 0:
        raise ValueError("panel_wp debe ser > 0")
    if dc_ac_ratio <= 0:
        raise ValueError("dc_ac_ratio debe ser > 0")
    if area_panel_m2 <= 0:
        raise ValueError("area_panel_m2 debe ser > 0")


def kwp_requerido_para_cobertura(
    *,
    kwh_mes: float,
    cobertura_obj: float = 0.75,
    hsp: float = 4.5,
    pr: float = 0.80,
    dias_mes: float = 30.0
) -> float:
    kwh_obj = float(kwh_mes) * float(cobertura_obj)
    return kwh_obj / (float(hsp) * float(pr) * float(dias_mes))


def config_tecnica_desde_kwp(
    *,
    kwp_objetivo: float,
    panel_wp: int = 550,
    dc_ac_ratio: float = 1.20,
    area_panel_m2: float = 2.6,
    factor_pasillos: float = 1.10,
    inv_kw_nom: Optional[float] = None
) -> Dict[str, Any]:
    panel_kw = float(panel_wp) / 1000.0
    n_paneles = max(1, int(math.ceil(float(kwp_objetivo) / panel_kw)))
    kwp_dc = n_paneles * panel_kw

    if inv_kw_nom is not None:
        inv_kw_ac = float(inv_kw_nom)
    else:
        inv_kw_teorico = kwp_dc / float(dc_ac_ratio)
        inv_kw_ac = seleccionar_inversor_kw(inv_kw_teorico)

    dc_ac = (kwp_dc / inv_kw_ac) if inv_kw_ac else None
    area_m2 = n_paneles * float(area_panel_m2)
    area_techo_m2 = area_m2 * float(factor_pasillos)

    return {
        "panel_wp": int(panel_wp),
        "n_paneles": int(n_paneles),
        "kwp_dc": round(float(kwp_dc), 2),
        "inv_kw_ac": float(inv_kw_ac),
        "dc_ac": round(float(dc_ac), 2) if dc_ac else None,
        "area_m2": round(float(area_m2), 1),
        "area_techo_m2": round(float(area_techo_m2), 1),
    }


def produccion_estimada(
    *,
    kwp_dc: float,
    hsp: float = 4.5,
    pr: float = 0.80,
    dias_mes: float = 30.0
) -> Dict[str, float]:
    kwh_dia = float(kwp_dc) * float(hsp) * float(pr)
    return {
        "kwh_dia": round(kwh_dia, 1),
        "kwh_mes": round(kwh_dia * float(dias_mes), 0),
        "kwh_anual": round(kwh_dia * 365.0, 0),
    }


def dimensionar_para_ahorro(
    *,
    kwh_mes: float,
    cobertura_obj: float = 0.75,
    hsp: float = 4.5,
    pr: float = 0.80,
    dias_mes: float = 30.0,
    panel_wp: int = 550,
    dc_ac_ratio: float = 1.20,
    area_panel_m2: float = 2.6,
    factor_pasillos: float = 1.10,
    inv_kw_nom: Optional[float] = None
) -> Dict[str, Any]:
    _validar_entrada_dimensionamiento(
        kwh_mes, cobertura_obj, hsp, pr, dias_mes, panel_wp, dc_ac_ratio, area_panel_m2
    )

    kwp_req = kwp_requerido_para_cobertura(
        kwh_mes=kwh_mes,
        cobertura_obj=cobertura_obj,
        hsp=hsp,
        pr=pr,
        dias_mes=dias_mes
    )

    cfg = config_tecnica_desde_kwp(
        kwp_objetivo=kwp_req,
        panel_wp=panel_wp,
        dc_ac_ratio=dc_ac_ratio,
        area_panel_m2=area_panel_m2,
        factor_pasillos=factor_pasillos,
        inv_kw_nom=inv_kw_nom
    )

    prod = produccion_estimada(kwp_dc=cfg["kwp_dc"], hsp=hsp, pr=pr, dias_mes=dias_mes)
    cobertura_real = min(1.0, float(prod["kwh_mes"]) / float(kwh_mes)) if kwh_mes else None

    return {
        "kwh_mes": float(kwh_mes),
        "cobertura_obj": float(cobertura_obj),
        "hsp": float(hsp),
        "pr": float(pr),
        "dias_mes": float(dias_mes),
        "kwp_req": round(float(kwp_req), 3),
        **cfg,
        **prod,
        "cobertura_real": round(float(cobertura_real), 3) if cobertura_real is not None else None,
    }


def calcular_configuracion_strings(
    *,
    n_paneles: int,
    vmp_mod: float,
    voc_mod: float,
    imp_mod: float,
    isc_mod: float,
    tc_voc_frac_c: float = -0.0029,
    n_mppt: int = 2,
    repartir_50_50: bool = True,
    vmppt_min: float = 200.0,
    vmppt_max: float = 800.0,
    vdc_max: float = 1000.0,
    imppt_max: float = 25.0,
    t_cell_ref_c: float = 25.0,
    t_min_c: float = 10.0,
    inv_kw_ac: float | None = None,
    vac: float = 240.0,
    fases: int = 1,
    fp: float = 1.0,
) -> Dict[str, Any]:

    n = int(n_paneles)
    if n <= 0:
        raise ValueError("n_paneles debe ser > 0")
    if n_mppt not in (1, 2):
        raise ValueError("n_mppt soportado: 1 o 2")

    if n_mppt == 1:
        grupos = [n]
    else:
        if repartir_50_50:
            n1 = (n + 1) // 2
            n2 = n // 2
        else:
            n1 = (n + 1) // 2
            n2 = n // 2
        grupos = [n1, n2]

    tc_abs = abs(float(tc_voc_frac_c))
    voc_factor_cold = 1.0 + tc_abs * (float(t_cell_ref_c) - float(t_min_c))

    checks = []
    strings = []

    for i_mppt, n_ser in enumerate(grupos, start=1):
        if n_ser <= 0:
            continue

        n_par = 1
        vmp_string = float(vmp_mod) * n_ser
        voc_string_stc = float(voc_mod) * n_ser
        voc_string_cold = voc_string_stc * voc_factor_cold

        imp_mppt = float(imp_mod) * n_par
        isc_mppt = float(isc_mod) * n_par

        if vmp_string < vmppt_min:
            checks.append(f"⚠️ MPPT {i_mppt}: Vmp_string={vmp_string:.0f} V < Vmppt_min={vmppt_min:.0f} V.")
        if vmp_string > vmppt_max:
            checks.append(f"⚠️ MPPT {i_mppt}: Vmp_string={vmp_string:.0f} V > Vmppt_max={vmppt_max:.0f} V.")
        if voc_string_cold > vdc_max:
            checks.append(f"❌ MPPT {i_mppt}: Voc_frio={voc_string_cold:.0f} V > Vdc_max={vdc_max:.0f} V.")
        if imp_mppt > imppt_max:
            checks.append(f"❌ MPPT {i_mppt}: Imp={imp_mppt:.1f} A > Imppt_max={imppt_max:.1f} A.")

        strings.append({
            "mppt": i_mppt,
            "n_series": n_ser,
            "n_paralelo": n_par,
            "vmp_string_v": vmp_string,
            "voc_string_stc_v": voc_string_stc,
            "voc_string_frio_v": voc_string_cold,
            "imp_a": imp_mppt,
            "isc_a": isc_mppt,
        })

    iac = None
    if inv_kw_ac is not None:
        p_w = float(inv_kw_ac) * 1000.0
        if fases == 3:
            iac = p_w / (math.sqrt(3) * float(vac) * float(fp))
        else:
            iac = p_w / (float(vac) * float(fp))

    return {
        "strings": strings,
        "checks": checks,
        "iac_estimada_a": iac,
        "params": {
            "voc_factor_frio": voc_factor_cold,
            "t_min_c": float(t_min_c),
            "vmppt_min": float(vmppt_min),
            "vmppt_max": float(vmppt_max),
            "vdc_max": float(vdc_max),
            "imppt_max": float(imppt_max),
        }
    }


def texto_config_electrica_pdf(cfg_strings: dict, *, etiqueta_izq="Techo izquierdo", etiqueta_der="Techo derecho") -> str:
    strings = cfg_strings.get("strings", [])
    checks = cfg_strings.get("checks", [])
    iac = cfg_strings.get("iac_estimada_a", None)

    etiquetas = {1: etiqueta_izq, 2: etiqueta_der}

    lines = ["<b>Configuración eléctrica referencial</b><br/>"]
    for s in strings:
        mppt = s["mppt"]
        nom = etiquetas.get(mppt, f"MPPT {mppt}")
        ns = s["n_series"]
        np = s["n_paralelo"]

        topologia = f"{ns} módulos en serie ({ns}S)" if np == 1 else f"{np} strings en paralelo de {ns}S ({ns}S×{np}P)"

        lines.append(
            f"• <b>{nom}</b> — {topologia}: "
            f"Vmp≈{s['vmp_string_v']:.0f} V | Voc frío≈{s['voc_string_frio_v']:.0f} V | Imp≈{s['imp_a']:.1f} A.<br/>"
        )

    if iac is not None:
        lines.append(f"• <b>Salida AC del inversor</b> — corriente estimada ≈ {iac:.1f} A.<br/>")

    if checks:
        lines.append("<br/><b>Notas de verificación</b><br/>")
        for c in checks:
            lines.append(f"• {c}<br/>")

    return "".join(lines)


def calcular_sizing_unificado(p: DatosProyecto) -> Dict[str, Any]:
    kwh_mes_prom = consumo_promedio(p.consumo_12m)

    sz = dimensionar_para_ahorro(
        kwh_mes=kwh_mes_prom,
        cobertura_obj=p.cobertura_objetivo,
        hsp=4.5,
        pr=0.80,
        dias_mes=30.0,
        panel_wp=550,
        dc_ac_ratio=1.20,
        area_panel_m2=2.6,
        factor_pasillos=1.10,
    )

    cfg_strings = calcular_configuracion_strings(
        n_paneles=int(sz["n_paneles"]),
        vmp_mod=float(sz.get("vmp_mod", 41.0)),
        voc_mod=float(sz.get("voc_mod", 49.5)),
        imp_mod=float(sz.get("imp_mod", 13.2)),
        isc_mod=float(sz.get("isc_mod", 14.0)),
        t_min_c=float(sz.get("t_min_c", 10.0)),
        n_mppt=2,
        repartir_50_50=True,
        vmppt_min=float(sz.get("inv_vmppt_min", 200)),
        vmppt_max=float(sz.get("inv_vmppt_max", 800)),
        vdc_max=float(sz.get("inv_vdc_max", 1000)),
        imppt_max=float(sz.get("inv_imppt_max", 25)),
        inv_kw_ac=float(sz["inv_kw_ac"]),
        vac=float(sz.get("vac", 240)),
        fases=int(sz.get("fases", 1)),
    )
    sz["cfg_strings"] = cfg_strings

    sz["capex_L"] = capex_L(float(sz["kwp_dc"]), p.costo_usd_kwp, p.tcambio)

    sz["kwp_recomendado"] = float(sz["kwp_dc"])
    sz["consumo_anual"] = consumo_anual(p.consumo_12m)
    sz["consumo_prom"] = float(kwh_mes_prom)

    return sz

