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
def _resumen_strings(rec: Dict[str, Any] | None) -> Dict[str, Any]:
    rec = rec or {}
    r = rec.get("recomendacion") or {}

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

    kwp_req = float(panel_sizing.kwp_req) if panel_sizing.ok else 0.0
    n_pan = int(panel_sizing.n_paneles) if panel_sizing.ok else 0
    pdc = float(panel_sizing.pdc_kw) if panel_sizing.ok else 0.0

    prod_anual_kwp = 0.0
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

    # ✅ SOLO inputs eléctricos para Paso 5 (NO NEC aquí)
    electrico_inputs = build_inputs_electricos_ui(p)

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

        "panel_id": _panel_id(eq),
        "inversor_recomendado": inv_id,
        "inversor_recomendado_meta": sizing_inv.get("inversor_recomendado_meta", {}),

        # strings NO aquí
        "strings_auto": {"ok": False, "warnings": ["Strings se calculan en Paso 5 (Ingeniería eléctrica)."]},

        "traza": _trazabilidad(
            eq, _panel_id(eq), inv_id, float(dc_ac),
            float(panel_sizing.hsp_prom), float(panel_sizing.pr)
        ),

        "panel_sizing": {
            "ok": bool(panel_sizing.ok),
            "errores": list(panel_sizing.errores),
            "hsp_12m": list(panel_sizing.hsp_12m),
            "hsp_prom": float(panel_sizing.hsp_prom),
            "pr": float(panel_sizing.pr),
            "meta": dict(panel_sizing.meta),
        },

        # ✅ inputs eléctricos para Paso 5
        "electrico_inputs": electrico_inputs,

        # útil para Paso 5 / NEC
        "pac_kw": float(pac_kw_fb),
    }

# core/inputs_electricos.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import streamlit as st


def build_inputs_electricos_ui(*, defaults: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    UI mínima para inputs eléctricos.
    Retorna un dict estable para que el orquestador/sizing no rompa.

    Ajusta campos según tu modelo real.
    """
    defaults = defaults or {}

    st.subheader("Inputs eléctricos (NEC / Ingeniería)")

    v_ll = st.number_input(
        "Voltaje AC (V)",
        min_value=100.0,
        max_value=1000.0,
        value=float(defaults.get("v_ac_v", 240.0)),
        step=10.0,
    )

    fases = st.selectbox(
        "Sistema",
        options=["1Φ", "3Φ"],
        index=0 if str(defaults.get("fases", "1Φ")) == "1Φ" else 1,
    )

    frec = st.number_input(
        "Frecuencia (Hz)",
        min_value=50.0,
        max_value=60.0,
        value=float(defaults.get("f_hz", 60.0)),
        step=1.0,
    )

    temp_amb = st.number_input(
        "Temperatura ambiente (°C)",
        min_value=-10.0,
        max_value=70.0,
        value=float(defaults.get("t_amb_c", 30.0)),
        step=1.0,
    )

    return {
        "v_ac_v": float(v_ll),
        "fases": str(fases),
        "f_hz": float(frec),
        "t_amb_c": float(temp_amb),
    }
