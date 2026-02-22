# core/sizing.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .modelo import Datosproyecto
from .simular_12_meses import capex_L, consumo_anual, consumo_promedio

from electrical.catalogos import get_panel, get_inversor, catalogo_inversores
from electrical.inversor.sizing_inversor import SizingInput, InversorCandidato, ejecutar_sizing
from electrical.paneles.sizing_panel import calcular_panel_sizing
from electrical.inversor.sizing_inversor import SizingInput, InversorCandidato, ejecutar_sizing


# ==========================================================
# Utilitarios (cortos)
# ==========================================================
def _safe_float(x: Any, default: float) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


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
# Sizing energético (kWp, n paneles) — EXTRAÍDO a electrical/sizing_panel.py
# ==========================================================
def _kwh_mes_prom(p: Datosproyecto) -> float:
    return float(consumo_promedio(p.consumo_12m))


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


def _recomendar_inversor(
    *,
    p: Datosproyecto,
    panel_w: float,
    dc_ac: float,
    prod_anual_kwp: float,
    pdc_obj_kw: Optional[float] = None,
) -> Dict[str, Any]:
    inp = SizingInput(
        consumo_anual_kwh=float(sum(p.consumo_12m)),
        produccion_anual_por_kwp_kwh=float(prod_anual_kwp),
        cobertura_obj=float(p.cobertura_objetivo),
        dc_ac_obj=float(dc_ac),
        pmax_panel_w=float(panel_w),
        # si tu sizing_electric ya fue actualizado, pasará; si no, ignora este argumento quitándolo
        pdc_obj_kw=pdc_obj_kw,
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
    dc_ac = _dc_ac_obj(eq)
    panel = get_panel(_panel_id(eq))

    # 1) sizing paneles (nuevo módulo)
    panel_sizing = calcular_panel_sizing(
        consumo_12m_kwh=list(p.consumo_12m),
        cobertura_obj=float(p.cobertura_objetivo),
        panel_w=float(panel.w),
        hsp_12m=getattr(p, "hsp_12m", None),
        hsp=getattr(p, "hsp", None),
        usar_modelo_hn_conservador=True,
        sombras_pct=_safe_float(getattr(p, "sombras_pct", 0.0), 0.0),
        perdidas_sistema_pct=getattr(p, "perdidas_sistema_pct", None),
        perdidas_detalle=getattr(p, "perdidas_detalle", None),
    )

    # Si falla sizing paneles, devolvemos igual con lo que haya para no romper UI
    kwp_req = float(panel_sizing.kwp_req) if panel_sizing.ok else 0.0
    n_pan = int(panel_sizing.n_paneles) if panel_sizing.ok else 0
    pdc = float(panel_sizing.pdc_kw) if panel_sizing.ok else 0.0

    # 2) recomendar inversor (usa producción anual por kWp según panel_sizing)
    prod_anual_kwp = 0.0
    # producción anual por kWp = sum(hsp_mes * pr * dias_mes)
    for hsp_d, dias in zip(panel_sizing.hsp_12m, panel_sizing.meta.get("dias_mes", [])):
        prod_anual_kwp += float(hsp_d) * float(panel_sizing.pr) * float(dias or 0)

    sizing_inv = _recomendar_inversor(
        p=p,
        panel_w=float(panel.w),
        dc_ac=float(dc_ac),
        prod_anual_kwp=float(prod_anual_kwp),
        pdc_obj_kw=float(pdc) if pdc > 0 else None,
    )

    inv_id_rec = sizing_inv.get("inversor_recomendado")
    inv_id = _inv_final(eq, inv_id_rec)
    inv = get_inversor(inv_id)

    pac_kw_fb = _pac_kw_desde_reco(
        sizing_inv.get("inversor_recomendado_meta", {}), inv_id
    ) or float(getattr(inv, "kw_ac", 0.0) or 0.0)

    # 3) strings
    rec = recomendar_string(
        panel=_panel_spec(panel),
        inversor=_inv_spec(inv, inv_id, pac_kw_fb),
        t_min_c=_safe_float(getattr(p, "t_min_c", 10.0), 10.0),
        objetivo_dc_ac=float(dc_ac),
        pdc_kw_objetivo=float(pdc) if pdc > 0 else float(pac_kw_fb) * float(dc_ac),
    )

    # 4) puente NEC (igual que antes)
    electrico = _build_electrico(p, panel, pac_kw_fb, rec)

    # 5) armado resultado (manteniendo llaves)
    kwh_mes = _kwh_mes_prom(p)
    prod_diaria_kwp = float(panel_sizing.hsp_prom) * float(panel_sizing.pr)

    return {
        "kwh_mes_prom": float(kwh_mes),
        "consumo_anual_kwh": float(consumo_anual(p.consumo_12m)),

        "kwp_req": round(float(kwp_req), 3),
        "n_paneles": int(n_pan),
        "pdc_kw": round(float(pdc), 3),

        "prod_anual_por_kwp_kwh": round(float(prod_anual_kwp), 2),
        "prod_diaria_por_kwp_kwh": round(float(prod_diaria_kwp), 3),

        "capex_L": capex_L(float(pdc), p.costo_usd_kwp, p.tcambio),

        "inversor_recomendado": inv_id,
        "inversor_recomendado_meta": sizing_inv.get("inversor_recomendado_meta", {}),

        "strings_auto": _resumen_strings(rec),

        "traza": _trazabilidad(eq, _panel_id(eq), inv_id, float(dc_ac), float(panel_sizing.hsp_prom), float(panel_sizing.pr)),

        # extra opcional (no rompe): dejar detalle sizing paneles para depurar/mostrar
        "panel_sizing": {
            "ok": bool(panel_sizing.ok),
            "errores": list(panel_sizing.errores),
            "hsp_12m": list(panel_sizing.hsp_12m),
            "hsp_prom": float(panel_sizing.hsp_prom),
            "pr": float(panel_sizing.pr),
            "meta": dict(panel_sizing.meta),
        },

        "electrico": electrico,
    }


def _build_electrico(p, panel, pac_kw, rec):
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

    temp_amb_c = float(ui_e.get("t_amb_c", 30.0)) if "t_amb_c" in ui_e else 30.0

    return {
        "n_strings": int(r.get("n_strings_total", 0) or 0),
        "isc_mod_a": float(getattr(panel, "isc", 0.0) or 0.0),
        "imp_mod_a": float(getattr(panel, "imp", 0.0) or 0.0),
        "vmp_string_v": float(r.get("vmp_string_v", 0.0) or 0.0),
        "voc_frio_string_v": float(r.get("voc_frio_string_v", 0.0) or 0.0),
        "p_ac_w": float(pac_kw) * 1000.0,

        "v_ac": vac,
        "fases": fases,
        "tension_sistema": tension,
        "pf_ac": float(ui_e.get("fp", 1.0)),

        "L_dc_string_m": float(ui_e.get("dist_dc_m", 10.0)),
        "L_dc_trunk_m": float(ui_e.get("dist_dc_trunk_m", 0.0)),
        "L_ac_m": float(ui_e.get("dist_ac_m", 15.0)),
        "vd_max_dc_pct": float(ui_e.get("vdrop_obj_dc_pct", 2.0)),
        "vd_max_ac_pct": float(ui_e.get("vdrop_obj_ac_pct", 2.0)),

        "temp_amb_c": float(temp_amb_c),
        "material": str(ui_e.get("material_conductor", "Cu")),
        "has_combiner": bool(ui_e.get("has_combiner", False)),
        "dc_arch": str(ui_e.get("dc_arch", "string_to_inverter")),

        "otros_ccc": int(ui_e.get("otros_ccc", 0)),
        "incluye_neutro_ac": bool(ui_e.get("incluye_neutro_ac", False)),
    }
