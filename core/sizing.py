# core/sizing.py
from __future__ import annotations

from typing import Any, Dict, Optional

from .modelo import Datosproyecto

from electrical.catalogos import get_panel
from electrical.paneles.dimensionado_paneles import calcular_panel_sizing
from core.consumo import consumo_anual_kwh, consumo_promedio_mensual_kwh, normalizar_cobertura
from electrical.inversor.orquestador_inversor import (
    ejecutar_inversor_desde_sizing,
)


# ==========================================================
# Helpers mínimos
# ==========================================================

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def _leer_equipos(p: Datosproyecto) -> Dict[str, Any]:
    eq = getattr(p, "equipos", None) or {}
    if not isinstance(eq, dict):
        raise ValueError("Formato inválido en p.equipos")
    return eq


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
# API pública — Sizing técnico puro
# ==========================================================

def calcular_sizing_unificado(
    p: Datosproyecto,
    params_fv: Dict[str, Any],
) -> Dict[str, Any]:

    # =========================
    # Equipos
    # =========================
    eq = _leer_equipos(p)

    panel = get_panel(_panel_id(eq))
    if panel is None:
        raise ValueError("Panel no encontrado en catálogo")

    panel_w = float(getattr(panel, "w", 0.0))
    if panel_w <= 0:
        raise ValueError("Potencia de panel inválida")

    dc_ac = _clamp(
        float(eq.get("sobredimension_dc_ac", 1.20)),
        1.00,
        2.00,
    )

    # =========================
    # Consumo
    # =========================
    consumo_12m_kwh = list(getattr(p, "consumo_12m", None) or [])
    if len(consumo_12m_kwh) != 12:
        raise ValueError("consumo_12m debe contener 12 valores")

    consumo_12m_kwh = [float(x or 0.0) for x in consumo_12m_kwh]

    consumo_anual_val = consumo_anual_kwh(consumo_12m_kwh)
    consumo_prom_val = consumo_promedio_mensual_kwh(consumo_12m_kwh)

    # =========================
    # Parámetros FV
    # =========================
    cobertura_obj = _clamp(
        float(params_fv.get("cobertura_obj", 1.0)),
        0.0,
        1.0,
    )

    hsp_12m = params_fv.get("hsp_12m")
    if hsp_12m is not None:
        if not isinstance(hsp_12m, (list, tuple)) or len(hsp_12m) != 12:
            raise ValueError("hsp_12m debe tener 12 valores")
        hsp_12m = [float(x or 0.0) for x in hsp_12m]

    # =========================
    # Modo dimensionamiento (desde UI)
    # =========================
    sf = getattr(p, "sistema_fv", {}) or {}

    modo_dimensionado = str(
        sf.get("modo_dimensionado", "auto")
    ).strip().lower()

    n_paneles_manual = None
    if modo_dimensionado == "manual":
        try:
            n_paneles_manual = int(sf.get("n_paneles_manual"))
            if n_paneles_manual <= 0:
                raise ValueError
        except Exception:
            raise ValueError("n_paneles_manual inválido en modo manual")

    # =========================
    # PANEL SIZING (motor unificado)
    # =========================
    panel_sizing = calcular_panel_sizing(
        consumo_12m_kwh=consumo_12m_kwh,
        cobertura_obj=cobertura_obj,
        panel_w=panel_w,
        modo=modo_dimensionado,
        n_paneles_manual=n_paneles_manual,
        hsp_12m=hsp_12m,
        hsp=params_fv.get("hsp"),
        usar_modelo_conservador=bool(params_fv.get("usar_modelo_conservador", False)),
        usar_modelo_hn_conservador=bool(params_fv.get("usar_modelo_hn_conservador", False)),
        sombras_pct=float(params_fv.get("sombras_pct", 0.0) or 0.0),
        perdidas_sistema_pct=float(params_fv.get("perdidas_sistema_pct", 0.0) or 0.0),
        perdidas_detalle=params_fv.get("perdidas_detalle"),
        params_fv=params_fv,
    )

    if not panel_sizing.ok:
        raise ValueError(f"Panel sizing inválido: {panel_sizing.errores}")

    kwp_req = float(panel_sizing.kwp_req)
    n_pan = int(panel_sizing.n_paneles)
    pdc = float(panel_sizing.pdc_kw)

    if n_pan <= 0 or pdc <= 0:
        raise ValueError("Sizing resultó en sistema inválido")

    prod_anual_kwp = float(
        panel_sizing.meta.get("prod_anual_por_kwp_kwh", 0.0)
    )

    if prod_anual_kwp <= 0:
        raise ValueError("Producción anual por kWp inválida")

    # =========================
    # INVERSOR
    # =========================
    resultado_inv = ejecutar_inversor_desde_sizing(
        consumo_anual_kwh=consumo_anual_val,
        prod_anual_por_kwp_kwh=prod_anual_kwp,
        cobertura_obj=cobertura_obj,
        dc_ac_obj=dc_ac,
        panel_w=panel_w,
        pdc_kw=pdc,
        inversor_id_forzado=_inv_id(eq),
    )

    # =========================
    # Salida técnica pura
    # =========================
    return {
        "modo_dimensionado": modo_dimensionado,
        "consumo_anual_kwh": consumo_anual_val,
        "consumo_promedio_kwh": consumo_prom_val,
        "kwp_req": round(kwp_req, 3),
        "n_paneles": n_pan,
        "pdc_kw": round(pdc, 3),
        "kwp_dc": round(pdc, 3),
        "prod_anual_por_kwp_kwh": round(prod_anual_kwp, 2),
        "panel_id": _panel_id(eq),
        "inversor_id": resultado_inv["inversor_id"],
        "pac_kw": resultado_inv["pac_kw"],
    }
