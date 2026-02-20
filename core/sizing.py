# nucleo/sizing.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .modelo import Datosproyecto
from .simular_12_meses import capex_L, consumo_anual, consumo_promedio

from electrical.catalogos import get_panel, get_inversor, catalogo_inversores
from electrical.sizing import SizingInput, InversorCandidato, ejecutar_sizing
from electrical.strings_auto import PanelSpec, InversorSpec, recomendar_string



# ==========================================================
# Constantes / defaults
# ==========================================================
T_STC_C = 25.0
DIAS_MES = 30.0


# ==========================================================
# Utilitarios (cortos)
# ==========================================================
def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def _pct_factor(pct: float) -> float:
    return 1.0 - float(pct) / 100.0


def _safe_float(x: Any, default: float) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _safe_int(x: Any, default: int) -> int:
    try:
        return int(x)
    except Exception:
        return int(default)


# ==========================================================
# Lectura Paso 3: HSP + PR
# ==========================================================
def _leer_hsp(p: Datosproyecto) -> float:
    return _clamp(_safe_float(getattr(p, "hsp", 4.5), 4.5), 0.5, 9.0)


def _leer_pr(p: Datosproyecto) -> float:
    perd = _safe_float(getattr(p, "perdidas_sistema_pct", 15.0), 15.0)
    sh = _safe_float(getattr(p, "sombras_pct", 0.0), 0.0)
    pr = _pct_factor(perd) * _pct_factor(sh)
    return _clamp(pr, 0.10, 1.00)


def _prod_anual_por_kwp(hsp: float, pr: float) -> float:
    return float(hsp) * float(pr) * 365.0


# ==========================================================
# Lectura Paso 4: equipos + objetivos
# ==========================================================
def _leer_equipos(p: Datosproyecto) -> Dict[str, Any]:
    eq = getattr(p, "equipos", None) or {}
    return eq if isinstance(eq, dict) else {}


def _dc_ac_obj(eq: Dict[str, Any]) -> float:
    return _clamp(_safe_float(eq.get("sobredimension_dc_ac", 1.20), 1.20), 1.00, 2.00)


def _panel_id(eq: Dict[str, Any]) -> str:
    return str(eq.get("panel_id") or "panel_550w")


def _inv_id(eq: Dict[str, Any]) -> Optional[str]:
    v = eq.get("inversor_id")
    return None if (v is None or str(v).strip() == "") else str(v)


# ==========================================================
# Sizing energético (kWp, n paneles)
# ==========================================================
def _kwh_mes_prom(p: Datosproyecto) -> float:
    return float(consumo_promedio(p.consumo_12m))


def _kwh_obj_mes(kwh_mes: float, cobertura_obj: float) -> float:
    return float(kwh_mes) * _clamp(float(cobertura_obj), 0.0, 1.0)


def _kwp_req(kwh_obj_mes: float, hsp: float, pr: float, dias_mes: float = DIAS_MES) -> float:
    denom = float(hsp) * float(pr) * float(dias_mes)
    if denom <= 0:
        raise ValueError("HSP/PR inválidos (denominador <= 0).")
    return float(kwh_obj_mes) / denom


def _n_paneles(kwp_req: float, panel_w: float) -> int:
    if panel_w <= 0:
        raise ValueError("Panel inválido (W<=0).")
    return max(1, int(math.ceil((float(kwp_req) * 1000.0) / float(panel_w))))


def _pdc_kw(n_paneles: int, panel_w: float) -> float:
    return (int(n_paneles) * float(panel_w)) / 1000.0


# ==========================================================
# Catálogo → candidatos inversor
# ==========================================================
def _candidatos_inversores() -> List[InversorCandidato]:
    out: List[InversorCandidato] = []
    for i in (catalogo_inversores() or []):
        out.append(_inv_dict_to_candidato(i))
    return out


def _inv_dict_to_candidato(i: Dict[str, Any]) -> InversorCandidato:
    return InversorCandidato(
        id=str(i["id"]),
        pac_kw=float(i["pac_kw"]),
        n_mppt=int(i["n_mppt"]),
        mppt_min_v=float(i["mppt_min_v"]),
        mppt_max_v=float(i["mppt_max_v"]),
        vdc_max_v=float(i["vmax_dc_v"]),
    )


def _recomendar_inversor(p: Datosproyecto, panel_w: float, dc_ac: float, prod_anual_kwp: float) -> Dict[str, Any]:
    inp = SizingInput(
        consumo_anual_kwh=float(sum(p.consumo_12m)),
        produccion_anual_por_kwp_kwh=float(prod_anual_kwp),
        cobertura_obj=float(p.cobertura_objetivo),
        dc_ac_obj=float(dc_ac),
        pmax_panel_w=float(panel_w),
    )
    return ejecutar_sizing(inp=inp, inversores_catalogo=_candidatos_inversores())


def _inv_final(eq: Dict[str, Any], inv_rec: Optional[str]) -> str:
    return str(_inv_id(eq) or inv_rec or "inv_5kw_2mppt")


# ==========================================================
# Resolver specs para strings_auto
# ==========================================================
def _panel_spec(panel: Any) -> PanelSpec:
    coef = float(getattr(panel, "coef_voc_pct_c", getattr(panel, "coef_voc", -0.28)))
    return PanelSpec(pmax_w=panel.w, vmp_v=panel.vmp, voc_v=panel.voc, imp_a=panel.imp, isc_a=panel.isc, coef_voc_pct_c=coef)


def _inv_spec(inv: Any, inv_ui_id: str, pac_kw_fallback: float) -> InversorSpec:
    pac_kw = float(getattr(inv, "kw_ac", pac_kw_fallback))
    imppt = float(getattr(inv, "imppt_max_a", getattr(inv, "imppt_max", 25.0)))
    return InversorSpec(
        pac_kw=pac_kw,
        vdc_max_v=float(inv.vdc_max),
        mppt_min_v=float(inv.vmppt_min),
        mppt_max_v=float(inv.vmppt_max),
        n_mppt=int(inv.n_mppt),
        imppt_max_a=imppt,
    )


def _pac_kw_desde_reco(meta: Dict[str, Any], inv_id: str) -> float:
    for c in (meta.get("candidatos") or []):
        if str(c.get("id")) == str(inv_id):
            return float(c.get("pac_kw", 0.0))
    return 0.0


# ==========================================================
# Resúmenes (UI/PDF)
# ==========================================================
def _resumen_strings(rec: Dict[str, Any]) -> Dict[str, Any]:
    r = (rec or {}).get("recomendacion") or {}
    return {
        "n_paneles_string": int(r.get("n_paneles_string", 0) or 0),
        "n_strings_total": int(r.get("n_strings_total", 0) or 0),
        "strings_por_mppt": int(r.get("strings_por_mppt", 0) or 0),
        "vmp_string_v": float(r.get("vmp_string_v", 0.0) or 0.0),
        "voc_frio_string_v": float(r.get("voc_frio_string_v", 0.0) or 0.0),
        "i_mppt_a": float(r.get("i_mppt_a", 0.0) or 0.0),
        "warnings": list(rec.get("warnings") or []),
        "errores": list(rec.get("errores") or []),
        "ok": bool(rec.get("ok", False)),
    }


def _trazabilidad(eq: Dict[str, Any], panel_id: str, inv_id: str, dc_ac: float, hsp: float, pr: float) -> Dict[str, Any]:
    return {
        "panel_id": panel_id,
        "inversor_id": inv_id,
        "dc_ac_objetivo": float(dc_ac),
        "hsp_usada": float(hsp),
        "pr_usado": float(pr),
    }


# ==========================================================
# API pública: ORQUESTA sizing unificado
# ==========================================================
def calcular_sizing_unificado(p: Datosproyecto) -> Dict[str, Any]:
    eq = _leer_equipos(p)
    hsp, pr = _leer_hsp(p), _leer_pr(p)
    dc_ac = _dc_ac_obj(eq)

    panel = get_panel(_panel_id(eq))
    prod_anual_kwp = _prod_anual_por_kwp(hsp, pr)

    kwh_mes = _kwh_mes_prom(p)
    kwp_req = _kwp_req(_kwh_obj_mes(kwh_mes, float(p.cobertura_objetivo)), hsp, pr)
    n_pan = _n_paneles(kwp_req, float(panel.w))
    pdc = _pdc_kw(n_pan, float(panel.w))

    sizing_inv = _recomendar_inversor(p, float(panel.w), dc_ac, prod_anual_kwp)
    inv_id_rec = sizing_inv.get("inversor_recomendado")
    inv_id = _inv_final(eq, inv_id_rec)

    inv = get_inversor(inv_id)
    pac_kw_fb = _pac_kw_desde_reco(sizing_inv.get("inversor_recomendado_meta", {}), inv_id) or float(getattr(inv, "kw_ac", 0.0) or 0.0)

    rec = recomendar_string(
        panel=_panel_spec(panel),
        inversor=_inv_spec(inv, inv_id, pac_kw_fb),
        t_min_c=_safe_float(getattr(p, "t_min_c", 10.0), 10.0),
        objetivo_dc_ac=float(dc_ac),
        pdc_kw_objetivo=float(pdc),
    )

    return {
        "kwh_mes_prom": float(kwh_mes),
        "consumo_anual_kwh": float(consumo_anual(p.consumo_12m)),
        "kwp_req": round(float(kwp_req), 3),
        "n_paneles": int(n_pan),
        "pdc_kw": round(float(pdc), 3),
        "capex_L": capex_L(float(pdc), p.costo_usd_kwp, p.tcambio),
        "inversor_recomendado": inv_id_rec,
        "inversor_recomendado_meta": sizing_inv.get("inversor_recomendado_meta", {}),
        "strings_auto": _resumen_strings(rec),
        "traza": _trazabilidad(eq, _panel_id(eq), inv_id, dc_ac, hsp, pr),
    }
