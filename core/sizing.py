# core/sizing.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .modelo import Datosproyecto
from .simular_12_meses import capex_L, consumo_anual, consumo_promedio

from electrical.catalogos import get_panel, get_inversor, catalogo_inversores
from electrical.inversor.sizing_inversor import SizingInput, InversorCandidato, ejecutar_sizing
from electrical.paneles.dimensionado_paneles import calcular_panel_sizing


# ==========================================================
# Utilitarios
# ==========================================================
def _safe_float(x: Any, default: float) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


# ==========================================================
# Lectura Paso 4
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
# Consumo promedio
# ==========================================================
def _kwh_mes_prom(p: Datosproyecto) -> float:
    return float(consumo_promedio(p.consumo_12m))


# ==========================================================
# Inversores candidatos
# ==========================================================
def _candidatos_inversores() -> List[InversorCandidato]:
    out: List[InversorCandidato] = []
    for i in (catalogo_inversores() or []):
        out.append(
            InversorCandidato(
                id=str(i["id"]),
                pac_kw=float(i["pac_kw"]),
                n_mppt=int(i["n_mppt"]),
                mppt_min_v=float(i["mppt_min_v"]),
                mppt_max_v=float(i["mppt_max_v"]),
                vdc_max_v=float(i.get("vdc_max", i.get("vmax_dc_v"))),
            )
        )
    return out


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
# API pública
# ==========================================================
def calcular_sizing_unificado(p: Datosproyecto) -> Dict[str, Any]:

    eq = _leer_equipos(p)
    dc_ac = _dc_ac_obj(eq)

    panel = get_panel(_panel_id(eq))

    sfv = getattr(p, "sistema_fv", None) or {}
    if not isinstance(sfv, dict):
        sfv = {}

    consumo_12m_kwh = list(getattr(p, "consumo_12m", None) or [])
    if len(consumo_12m_kwh) != 12:
        consumo_12m_kwh = (consumo_12m_kwh + [0.0] * 12)[:12]
    consumo_12m_kwh = [float(x or 0.0) for x in consumo_12m_kwh]

    cobertura_obj = sfv.get("cobertura_obj", sfv.get("cobertura", 1.0))
    try:
        cobertura_obj = float(cobertura_obj)
    except Exception:
        cobertura_obj = 1.0
    if cobertura_obj > 1.0:
        cobertura_obj /= 100.0
    cobertura_obj = max(0.0, min(1.0, cobertura_obj))

    hsp_12m = sfv.get("hsp_12m", None)
    if isinstance(hsp_12m, (list, tuple)) and len(hsp_12m) == 12:
        try:
            hsp_12m = [float(x or 0.0) for x in hsp_12m]
        except Exception:
            hsp_12m = None
    else:
        hsp_12m = None

    panel_w = float(getattr(panel, "w", 550.0))

    # =========================
    # PANEL SIZING
    # =========================
    panel_sizing = calcular_panel_sizing(
        consumo_12m_kwh=consumo_12m_kwh,
        cobertura_obj=cobertura_obj,
        panel_w=panel_w,
        hsp_12m=hsp_12m,
        hsp=sfv.get("hsp"),
        usar_modelo_conservador=bool(sfv.get("usar_modelo_conservador", False)),
        usar_modelo_hn_conservador=bool(sfv.get("usar_modelo_hn_conservador", False)),
        sombras_pct=float(sfv.get("sombras_pct", 0.0) or 0.0),
        perdidas_sistema_pct=float(sfv.get("perdidas_sistema_pct", 0.0) or 0.0),
        perdidas_detalle=sfv.get("perdidas_detalle"),
    )

    if not panel_sizing.ok:
        return {}

    kwp_req = float(panel_sizing.kwp_req or 0.0)
    n_pan = int(panel_sizing.n_paneles or 0)
    pdc = float(panel_sizing.pdc_kw or 0.0)

    # Producción anual estimada
    prod_anual_kwp = 0.0
    try:
        dias_mes = list((panel_sizing.meta or {}).get("dias_mes", []))
        for hsp_d, dias in zip(panel_sizing.hsp_12m, dias_mes):
            prod_anual_kwp += float(hsp_d or 0.0) * float(panel_sizing.pr or 0.0) * float(dias or 0.0)
    except Exception:
        pass

    # =========================
    # INVERSOR
    # =========================
    sizing_inv = _recomendar_inversor(
        p=p,
        panel_w=panel_w,
        dc_ac=dc_ac,
        prod_anual_kwp=prod_anual_kwp,
        pdc_obj_kw=pdc if pdc > 0 else None,
    )

    inv_id_rec = sizing_inv.get("inversor_recomendado")
    inv_id = _inv_final(eq, inv_id_rec)
    inv = get_inversor(inv_id)

    pac_kw_fb = (
        _pac_kw_desde_reco(
            sizing_inv.get("inversor_recomendado_meta", {}), inv_id
        )
        or float(getattr(inv, "kw_ac", 0.0) or 0.0)
    )

    return {
        "kwh_mes_prom": float(_kwh_mes_prom(p)),
        "consumo_anual_kwh": float(consumo_anual(p.consumo_12m)),

        "kwp_req": round(kwp_req, 3),
        "n_paneles": n_pan,
        "pdc_kw": round(pdc, 3),

        "prod_anual_por_kwp_kwh": round(prod_anual_kwp, 2),

        "capex_L": capex_L(pdc, p.costo_usd_kwp, p.tcambio),

        "panel_id": _panel_id(eq),
        "inversor_recomendado": inv_id,
        "inversor_recomendado_meta": sizing_inv.get("inversor_recomendado_meta", {}),

        "pac_kw": float(pac_kw_fb),
    }
