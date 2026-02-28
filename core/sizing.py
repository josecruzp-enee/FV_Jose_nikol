# core/sizing.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .modelo import Datosproyecto
from .simular_12_meses import capex_L, consumo_anual, consumo_promedio

from electrical.catalogos import get_panel, get_inversor, catalogo_inversores
from electrical.inversor.sizing_inversor import SizingInput, InversorCandidato, ejecutar_sizing
from electrical.paneles.dimensionado_paneles import calcular_panel_sizing


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
    # default 1.20, clamp 1.00-2.00
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
        # si tu sizing_inversor acepta esto, se usa; si no, bórralo aquí y en SizingInput
        pdc_obj_kw=pdc_obj_kw,
    )
    return ejecutar_sizing(inp=inp, inversores_catalogo=_candidatos_inversores())


def _inv_final(eq: Dict[str, Any], inv_rec: Optional[str]) -> str:
    return str(_inv_id(eq) or inv_rec or "inv_5kw_2mppt")


def _pac_kw_desde_reco(meta: Dict[str, Any], inv_id: str) -> float:
    for c in (meta.get("candidatos") or []):
        if str(c.get("id")) == str(inv_id):
            return float(c.get("pac_kw", 0.0))
    return 0.0


# ==========================================================
# Inputs eléctricos (mapper puro para Paso 5)
# ==========================================================
def build_inputs_electricos_ui(p: Datosproyecto) -> Dict[str, Any]:
    """
    NO es UI de Streamlit. Solo normaliza lo que venga en p.electrico/equipos
    a un contrato estable para Paso 5 / paquete NEC.
    """
    ui_e = getattr(p, "electrico", {}) or {}
    if not isinstance(ui_e, dict):
        ui_e = {}

    eq = getattr(p, "equipos", {}) or {}
    if not isinstance(eq, dict):
        eq = {}

    vac = float(ui_e.get("vac", 240.0))
    fases = int(ui_e.get("fases", 1))
    fp = float(ui_e.get("fp", 1.0))

    tension_sistema = str(eq.get("tension_sistema", "2F+N_120/240"))

    # Regla simple: 1φ => vac_ln ; 3φ => vac_ll
    vac_ln = vac if fases == 1 else None
    vac_ll = vac if fases == 3 else None

    t_amb_c = float(ui_e.get("t_amb_c", 30.0)) if "t_amb_c" in ui_e else 30.0

    return {
        # --- AC base ---
        "fases": fases,
        "fp": fp,
        "vac_ln": vac_ln,
        "vac_ll": vac_ll,
        # --- instalación ---
        "tension_sistema": tension_sistema,
        "dist_dc_m": float(ui_e.get("dist_dc_m", 10.0)),
        "dist_dc_trunk_m": float(ui_e.get("dist_dc_trunk_m", 0.0)),
        "dist_ac_m": float(ui_e.get("dist_ac_m", 15.0)),
        "vdrop_obj_dc_pct": float(ui_e.get("vdrop_obj_dc_pct", 2.0)),
        "vdrop_obj_ac_pct": float(ui_e.get("vdrop_obj_ac_pct", 2.0)),
        "t_amb_c": float(t_amb_c),
        "material_conductor": str(ui_e.get("material_conductor", "Cu")),
        "has_combiner": bool(ui_e.get("has_combiner", False)),
        "dc_arch": str(ui_e.get("dc_arch", "string_to_inverter")),
        "otros_ccc": int(ui_e.get("otros_ccc", 0)),
        "incluye_neutro_ac": bool(ui_e.get("incluye_neutro_ac", False)),
    }


# ==========================================================
# API pública: ORQUESTA sizing unificado
# ==========================================================
def calcular_sizing_unificado(p: Datosproyecto) -> Dict[str, Any]:
    eq = _leer_equipos(p)
    dc_ac = _dc_ac_obj(eq)

    # Catálogo (panel elegido por UI)
    panel = get_panel(_panel_id(eq))

    # =========================
    # Entradas desde sistema_fv
    # =========================
    sfv = getattr(p, "sistema_fv", None) or {}
    if not isinstance(sfv, dict):
        sfv = {}

    # consumo_12m_kwh (lista 12) desde p.consumo_12m (canónico)
    consumo_12m_kwh = list(getattr(p, "consumo_12m", None) or [])
    if len(consumo_12m_kwh) != 12:
        consumo_12m_kwh = (consumo_12m_kwh + [0.0] * 12)[:12]
    consumo_12m_kwh = [float(x or 0.0) for x in consumo_12m_kwh]

    # cobertura objetivo (0..1). Si viene en %, normalizamos.
    cobertura_obj = sfv.get("cobertura_obj", sfv.get("cobertura", 1.0))
    try:
        cobertura_obj = float(cobertura_obj)
    except Exception:
        cobertura_obj = 1.0
    if cobertura_obj > 1.0:
        cobertura_obj = cobertura_obj / 100.0
    cobertura_obj = max(0.0, min(1.0, cobertura_obj))

    # hsp_12m: preferir lo que venga de sistema_fv; si no, None (dimensionado_paneles decide)
    hsp_12m = sfv.get("hsp_12m", None)
    if isinstance(hsp_12m, (list, tuple)) and len(hsp_12m) == 12:
        try:
            hsp_12m = [float(x or 0.0) for x in hsp_12m]
        except Exception:
            hsp_12m = None
    else:
        hsp_12m = None

    # panel_w: primero desde el panel seleccionado en catálogo; si no, fallback en sistema_fv
    panel_w = None
    try:
        panel_w = float(getattr(panel, "w"))
    except Exception:
        panel_w = None

    if panel_w is None:
        try:
            panel_w = float(sfv.get("panel_w", sfv.get("potencia_panel_w", 550.0)))
        except Exception:
            panel_w = 550.0

    # =========================
    # Panel sizing (OBLIGATORIOS: cobertura_obj, panel_w)
    # =========================
    panel_sizing = calcular_panel_sizing(
        consumo_12m_kwh=consumo_12m_kwh,
        cobertura_obj=cobertura_obj,   # ✅ obligatorio
        panel_w=panel_w,               # ✅ obligatorio
        hsp_12m=hsp_12m,
        hsp=sfv.get("hsp"),
        usar_modelo_conservador=bool(sfv.get("usar_modelo_conservador", False)),
        usar_modelo_hn_conservador=bool(sfv.get("usar_modelo_hn_conservador", False)),
        sombras_pct=float(sfv.get("sombras_pct", 0.0) or 0.0),
        perdidas_sistema_pct=float(sfv.get("perdidas_sistema_pct", 0.0) or 0.0),
        perdidas_detalle=sfv.get("perdidas_detalle"),
    )

    kwp_req = float(getattr(panel_sizing, "kwp_req", 0.0)) if panel_sizing.ok else 0.0
    n_pan = int(getattr(panel_sizing, "n_paneles", 0)) if panel_sizing.ok else 0
    pdc = float(getattr(panel_sizing, "pdc_kw", 0.0)) if panel_sizing.ok else 0.0

    # Producción anual por kWp (kWh/kWp-año)
    prod_anual_kwp = 0.0
    try:
        dias_mes = list((panel_sizing.meta or {}).get("dias_mes", []))
        for hsp_d, dias in zip(panel_sizing.hsp_12m, dias_mes):
            prod_anual_kwp += float(hsp_d or 0.0) * float(panel_sizing.pr or 0.0) * float(dias or 0.0)
    except Exception:
        prod_anual_kwp = 0.0

    # =========================
    # Recomendación inversor
    # =========================
    sizing_inv = _recomendar_inversor(
        p=p,
        panel_w=float(panel_w),
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

    # Inputs eléctricos para Paso 5
    electrico_inputs = build_inputs_electricos_ui(p)

    kwh_mes = _kwh_mes_prom(p)
    prod_diaria_kwp = float(getattr(panel_sizing, "hsp_prom", 0.0) or 0.0) * float(getattr(panel_sizing, "pr", 0.0) or 0.0)

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

        # Strings NO aquí
        "strings": {"ok": False, "warnings": ["Strings se calculan en Paso 5 (Ingeniería eléctrica)."]},

        "traza": {
            "panel_id": _panel_id(eq),
            "inversor_id": inv_id,
            "dc_ac_objetivo": float(dc_ac),
            "hsp_usada": float(getattr(panel_sizing, "hsp_prom", 0.0) or 0.0),
            "pr_usado": float(getattr(panel_sizing, "pr", 0.0) or 0.0),
        },

        "panel_sizing": {
            "ok": bool(getattr(panel_sizing, "ok", False)),
            "errores": list(getattr(panel_sizing, "errores", []) or []),
            "hsp_12m": list(getattr(panel_sizing, "hsp_12m", []) or []),
            "hsp_prom": float(getattr(panel_sizing, "hsp_prom", 0.0) or 0.0),
            "pr": float(getattr(panel_sizing, "pr", 0.0) or 0.0),
            "meta": dict(getattr(panel_sizing, "meta", {}) or {}),
        },

        "electrico_inputs": electrico_inputs,

        # útil para Paso 5 / NEC
        "pac_kw": float(pac_kw_fb),
    }
