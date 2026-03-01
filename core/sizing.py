# core/sizing.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .modelo import Datosproyecto
from .simular_12_meses import capex_L, consumo_anual

from electrical.catalogos import get_panel, get_inversor, catalogo_inversores
from electrical.inversor.sizing_inversor import (
    SizingInput,
    InversorCandidato,
    ejecutar_sizing,
)
from electrical.paneles.dimensionado_paneles import calcular_panel_sizing


# ==========================================================
# Utilitarios seguros
# ==========================================================

def _safe_float(x: Any, default: float) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


# ==========================================================
# Lectura equipos
# ==========================================================

def _leer_equipos(p: Datosproyecto) -> Dict[str, Any]:
    eq = getattr(p, "equipos", None) or {}
    if not isinstance(eq, dict):
        raise ValueError("Formato inválido en p.equipos")
    return eq


def _dc_ac_obj(eq: Dict[str, Any]) -> float:
    return _clamp(_safe_float(eq.get("sobredimension_dc_ac", 1.20), 1.20), 1.00, 2.00)


def _panel_id(eq: Dict[str, Any]) -> str:
    pid = str(eq.get("panel_id") or "").strip()
    if not pid:
        raise ValueError("panel_id no definido en equipos")
    return pid


def _inv_id(eq: Dict[str, Any]) -> Optional[str]:
    v = eq.get("inversor_id")
    if v is None:
        return None
    v = str(v).strip()
    return v if v else None


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
    if not out:
        raise ValueError("Catálogo de inversores vacío")
    return out


def _recomendar_inversor(
    *,
    p: Datosproyecto,
    panel_w: float,
    dc_ac: float,
    prod_anual_kwp: float,
    pdc_obj_kw: Optional[float],
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


def _pac_kw_desde_reco(meta: Dict[str, Any], inv_id: str) -> float:
    for c in (meta.get("candidatos") or []):
        if str(c.get("id")) == str(inv_id):
            return float(c.get("pac_kw", 0.0))
    return 0.0


# ==========================================================
# API pública
# ==========================================================

def calcular_sizing_unificado(
    p: Datosproyecto,
    params_fv: Dict[str, Any],
) -> Dict[str, Any]:

    # =========================
    # Equipos
    # =========================
    eq = _leer_equipos(p)
    dc_ac = _dc_ac_obj(eq)

    panel = get_panel(_panel_id(eq))
    if panel is None:
        raise ValueError("Panel no encontrado en catálogo")

    panel_w = float(getattr(panel, "w", 0.0))
    if panel_w <= 0:
        raise ValueError("Potencia de panel inválida")

    # =========================
    # Consumo
    # =========================
    consumo_12m_kwh = list(getattr(p, "consumo_12m", None) or [])
    if len(consumo_12m_kwh) != 12:
        raise ValueError("consumo_12m debe contener 12 valores")

    consumo_12m_kwh = [float(x or 0.0) for x in consumo_12m_kwh]

    # =========================
    # Parámetros FV explícitos
    # =========================
    cobertura_obj = float(params_fv.get("cobertura_obj", 1.0))
    cobertura_obj = max(0.0, min(1.0, cobertura_obj))

    hsp_12m = params_fv.get("hsp_12m")
    if hsp_12m is not None:
        if not isinstance(hsp_12m, (list, tuple)) or len(hsp_12m) != 12:
            raise ValueError("hsp_12m debe tener 12 valores")
        hsp_12m = [float(x or 0.0) for x in hsp_12m]

    # =========================
    # PANEL SIZING
    # =========================
    panel_sizing = calcular_panel_sizing(
        consumo_12m_kwh=consumo_12m_kwh,
        cobertura_obj=cobertura_obj,
        panel_w=panel_w,
        hsp_12m=hsp_12m,
        hsp=params_fv.get("hsp"),
        usar_modelo_conservador=bool(params_fv.get("usar_modelo_conservador", False)),
        usar_modelo_hn_conservador=bool(params_fv.get("usar_modelo_hn_conservador", False)),
        sombras_pct=float(params_fv.get("sombras_pct", 0.0) or 0.0),
        perdidas_sistema_pct=float(params_fv.get("perdidas_sistema_pct", 0.0) or 0.0),
        perdidas_detalle=params_fv.get("perdidas_detalle"),
    )

    if not panel_sizing.ok:
        raise ValueError(f"Panel sizing inválido: {panel_sizing.errores}")

    kwp_req = float(panel_sizing.kwp_req)
    n_pan = int(panel_sizing.n_paneles)
    pdc = float(panel_sizing.pdc_kw)

    if n_pan <= 0 or pdc <= 0:
        raise ValueError("Sizing resultó en sistema inválido")

    # =========================
    # Producción anual estimada
    # =========================
    prod_anual_kwp = float(panel_sizing.meta.get("prod_anual_por_kwp_kwh", 0.0))
    if prod_anual_kwp <= 0:
        raise ValueError("Producción anual por kWp inválida")

    # =========================
    # INVERSOR
    # =========================
    sizing_inv = _recomendar_inversor(
        p=p,
        panel_w=panel_w,
        dc_ac=dc_ac,
        prod_anual_kwp=prod_anual_kwp,
        pdc_obj_kw=pdc,
    )

    inv_id_rec = sizing_inv.get("inversor_recomendado")
    inv_id_final = _inv_id(eq) or inv_id_rec

    if not inv_id_final:
        raise ValueError("No se pudo determinar inversor recomendado")

    inv = get_inversor(inv_id_final)
    if inv is None:
        raise ValueError("Inversor no encontrado en catálogo")

    pac_kw_fb = (
        _pac_kw_desde_reco(
            sizing_inv.get("inversor_recomendado_meta", {}),
            inv_id_final,
        )
        or float(getattr(inv, "kw_ac", 0.0))
    )

    if pac_kw_fb <= 0:
        raise ValueError("Potencia AC inválida en inversor")

    # =========================
    # Salida final estable
    # =========================
    return {
        "consumo_anual_kwh": float(consumo_anual(p.consumo_12m)),

        "kwp_req": round(kwp_req, 3),
        "n_paneles": n_pan,
        "pdc_kw": round(pdc, 3),

        "prod_anual_por_kwp_kwh": round(prod_anual_kwp, 2),

        "capex_L": capex_L(pdc, p.costo_usd_kwp, p.tcambio),

        "panel_id": _panel_id(eq),

        "inversor_recomendado": inv_id_final,
        "inversor_recomendado_meta": sizing_inv.get("inversor_recomendado_meta", {}),

        "pac_kw": float(pac_kw_fb),
    }
