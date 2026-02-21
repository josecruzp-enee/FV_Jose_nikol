# core/sizing.py
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .modelo import Datosproyecto
from .simular_12_meses import capex_L, consumo_anual, consumo_promedio

from electrical.catalogos import get_panel, get_inversor, catalogo_inversores
from electrical.sizing_electric import SizingInput, InversorCandidato, ejecutar_sizing
from electrical.strings_auto import PanelSpec, InversorSpec, recomendar_string


# ==========================================================
# Constantes / defaults
# ==========================================================
T_STC_C = 25.0
DIAS_MES = 30.0  # (legacy) ya no se usa para sizing, se mantiene por compat si alguien lo usa


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
#   NOTA: Antes se dimensionaba por "mes promedio" con DIAS_MES=30.
#         Ahora se dimensiona por ENERGÍA ANUAL para evitar sesgo de días/mes.
# ==========================================================
def _kwh_mes_prom(p: Datosproyecto) -> float:
    return float(consumo_promedio(p.consumo_12m))


def _kwh_obj_mes(kwh_mes: float, cobertura_obj: float) -> float:
    # (legacy) se deja por compat; ya no se usa para sizing principal
    return float(kwh_mes) * _clamp(float(cobertura_obj), 0.0, 1.0)


def _kwp_req(kwh_obj_mes: float, hsp: float, pr: float, dias_mes: float = DIAS_MES) -> float:
    # (legacy) se deja por compat; ya no se usa en el sizing principal
    denom = float(hsp) * float(pr) * float(dias_mes)
    if denom <= 0:
        raise ValueError("HSP/PR inválidos (denominador <= 0).")
    return float(kwh_obj_mes) / denom


def _kwh_obj_anual(consumo_anual_kwh: float, cobertura_obj: float) -> float:
    return float(consumo_anual_kwh) * _clamp(float(cobertura_obj), 0.0, 1.0)


def _kwp_req_anual(kwh_obj_anual: float, hsp: float, pr: float) -> float:
    denom = float(hsp) * float(pr) * 365.0
    if denom <= 0:
        raise ValueError("HSP/PR inválidos (denominador <= 0).")
    return float(kwh_obj_anual) / denom


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
    return PanelSpec(
        pmax_w=panel.w,
        vmp_v=panel.vmp,
        voc_v=panel.voc,
        imp_a=panel.imp,
        isc_a=panel.isc,
        coef_voc_pct_c=coef,
    )


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
    panel, hsp, pr, dc_ac = _base_inputs(p, eq)
    kwh_mes, kwp_req, n_pan, pdc = _sizing_energetico(p, panel, hsp, pr)
    inv, inv_id, pac_kw_fb, sizing_inv = _resolver_inversor(p, eq, panel, dc_ac, hsp, pr)
    rec = _calcular_strings(p, panel, inv, inv_id, pac_kw_fb, dc_ac, pdc)
    electrico = _build_electrico(p, panel, pac_kw_fb, rec)

    return _armar_resultado(
        p, eq, panel, inv_id, dc_ac, hsp, pr,
        kwh_mes, kwp_req, n_pan, pdc,
        sizing_inv, rec, electrico
    )


# ==========================================================
# Helpers (≤10 líneas cada uno)
# ==========================================================
def _base_inputs(p, eq):
    hsp, pr = _leer_hsp(p), _leer_pr(p)
    dc_ac = _dc_ac_obj(eq)
    panel = get_panel(_panel_id(eq))
    return panel, hsp, pr, dc_ac


def _sizing_energetico(p, panel, hsp, pr):
    """
    Sizing principal por energía ANUAL (reduce sesgo de días/mes).
    Se mantiene kwh_mes_prom solo para reporting/UI.
    """
    kwh_anual = float(consumo_anual(p.consumo_12m))
    kwh_obj_anual = _kwh_obj_anual(kwh_anual, p.cobertura_objetivo)
    kwp_req = _kwp_req_anual(kwh_obj_anual, hsp, pr)

    n_pan = _n_paneles(kwp_req, panel.w)
    pdc = _pdc_kw(n_pan, panel.w)

    kwh_mes = _kwh_mes_prom(p)  # referencia
    return kwh_mes, kwp_req, n_pan, pdc


def _resolver_inversor(p, eq, panel, dc_ac, hsp, pr):
    prod = _prod_anual_por_kwp(hsp, pr)
    sizing_inv = _recomendar_inversor(p, panel.w, dc_ac, prod)
    inv_id_rec = sizing_inv.get("inversor_recomendado")
    inv_id = _inv_final(eq, inv_id_rec)
    inv = get_inversor(inv_id)
    pac_kw_fb = _pac_kw_desde_reco(
        sizing_inv.get("inversor_recomendado_meta", {}), inv_id
    ) or float(getattr(inv, "kw_ac", 0.0) or 0.0)
    return inv, inv_id, pac_kw_fb, sizing_inv


def _calcular_strings(p, panel, inv, inv_id, pac_kw_fb, dc_ac, pdc):
    return recomendar_string(
        panel=_panel_spec(panel),
        inversor=_inv_spec(inv, inv_id, pac_kw_fb),
        t_min_c=_safe_float(getattr(p, "t_min_c", 10.0), 10.0),
        objetivo_dc_ac=float(dc_ac),
        pdc_kw_objetivo=float(pdc),
    )


def _build_electrico(p, panel, pac_kw, rec):
    """
    Este dict es el puente SIZING → NEC.
    Debe contener:
      - mínimos NEC: n_strings, isc_mod_a, imp_mod_a, vmp_string_v, voc_frio_string_v, p_ac_w
      - y además parámetros AC/cableado targets (vd%, L, pf, sistema)
    """
    r = (rec or {}).get("recomendacion") or {}
    ui_e = getattr(p, "electrico", {}) or {}
    if not isinstance(ui_e, dict):
        ui_e = {}

    vac = float(ui_e.get("vac", 240.0))
    fases = int(ui_e.get("fases", 1))

    eq = getattr(p, "equipos", {}) or {}
    if not isinstance(eq, dict):
        eq = {}
    tension = str(eq.get("tension_sistema", "2F+N_120/240"))

    # Importante: temp_amb_c NO es t_min_c (t_min es para Voc frío)
    temp_amb_c = float(ui_e.get("t_amb_c", 30.0)) if "t_amb_c" in ui_e else 30.0

    return {
        # -------------------------
        # Mínimos NEC (tu adapter los exige)
        # -------------------------
        "n_strings": int(r.get("n_strings_total", 0) or 0),
        "isc_mod_a": float(getattr(panel, "isc", 0.0) or 0.0),
        "imp_mod_a": float(getattr(panel, "imp", 0.0) or 0.0),
        "vmp_string_v": float(r.get("vmp_string_v", 0.0) or 0.0),
        "voc_frio_string_v": float(r.get("voc_frio_string_v", 0.0) or 0.0),
        "p_ac_w": float(pac_kw) * 1000.0,

        # -------------------------
        # AC / sistema
        # -------------------------
        "v_ac": vac,
        "fases": fases,
        "tension_sistema": tension,
        "pf_ac": float(ui_e.get("fp", 1.0)),

        # -------------------------
        # Cableado / targets (para NEC)
        # -------------------------
        "L_dc_string_m": float(ui_e.get("dist_dc_m", 10.0)),
        "L_dc_trunk_m": float(ui_e.get("dist_dc_trunk_m", 0.0)),  # opcional
        "L_ac_m": float(ui_e.get("dist_ac_m", 15.0)),
        "vd_max_dc_pct": float(ui_e.get("vdrop_obj_dc_pct", 2.0)),
        "vd_max_ac_pct": float(ui_e.get("vdrop_obj_ac_pct", 2.0)),

        # Ambiente/material/arquitectura (defaults seguros)
        "temp_amb_c": float(temp_amb_c),
        "material": str(ui_e.get("material_conductor", "Cu")),
        "has_combiner": bool(ui_e.get("has_combiner", False)),
        "dc_arch": str(ui_e.get("dc_arch", "string_to_inverter")),

        # Extras UI (por si tu NEC los usa o para trazabilidad)
        "otros_ccc": int(ui_e.get("otros_ccc", 0)),
        "incluye_neutro_ac": bool(ui_e.get("incluye_neutro_ac", False)),
    }


def _armar_resultado(
    p, eq, panel, inv_id, dc_ac, hsp, pr,
    kwh_mes, kwp_req, n_pan, pdc,
    sizing_inv, rec, electrico
):
    # Extras útiles para UI/PDF (no rompen contrato: solo agregan campos)
    prod_anual_kwp = _prod_anual_por_kwp(hsp, pr)          # kWh/kWp-año
    prod_diaria_kwp = float(hsp) * float(pr)               # kWh/kWp-día (promedio)

    return {
        "kwh_mes_prom": float(kwh_mes),
        "consumo_anual_kwh": float(consumo_anual(p.consumo_12m)),

        # sizing
        "kwp_req": round(float(kwp_req), 3),
        "n_paneles": int(n_pan),
        "pdc_kw": round(float(pdc), 3),

        # trazabilidad energética (nuevo)
        "prod_anual_por_kwp_kwh": round(float(prod_anual_kwp), 2),
        "prod_diaria_por_kwp_kwh": round(float(prod_diaria_kwp), 3),

        # costos
        "capex_L": capex_L(float(pdc), p.costo_usd_kwp, p.tcambio),

        # inversor
        "inversor_recomendado": inv_id,
        "inversor_recomendado_meta": sizing_inv.get("inversor_recomendado_meta", {}),

        # strings
        "strings_auto": _resumen_strings(rec),

        # traza inputs clave
        "traza": _trazabilidad(eq, _panel_id(eq), inv_id, dc_ac, hsp, pr),

        # puente hacia NEC
        "electrico": electrico,  # <-- CLAVE: puente hacia adaptador_nec
    }
