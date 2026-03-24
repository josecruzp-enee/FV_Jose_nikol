from __future__ import annotations

"""
Servicio de sizing FV.
"""

from typing import Any, Dict, Optional, List
from math import ceil

from core.dominio.modelo import Datosproyecto
from core.dominio.contrato import ResultadoSizing, MesEnergia

from core.servicios.consumo import (
    consumo_anual_kwh,
    consumo_promedio_mensual_kwh,
    normalizar_cobertura,
)

from electrical.catalogos import get_panel
from electrical.inversor.orquestador_inversor import (
    ejecutar_inversor_desde_sizing,
)

from electrical.paneles.dimensionado_paneles import dimensionar_paneles


# ==========================================================
# Helpers internos
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
# Lectura base
# ==========================================================

def _leer_panel_y_config(p: Datosproyecto):

    eq = _leer_equipos(p)

    panel = get_panel(_panel_id(eq))

    if panel is None:
        raise ValueError("Panel no encontrado en catálogo")

    panel_w = float(getattr(panel, "pmax_w", 0.0))

    if panel_w <= 0:
        raise ValueError("Potencia de panel inválida")

    dc_ac_obj = _clamp(
        float(eq.get("sobredimension_dc_ac", 1.20)),
        1.00,
        2.00,
    )

    return panel, dc_ac_obj, eq


def _leer_consumo_y_cobertura(p: Datosproyecto):

    consumo_12m_kwh = list(getattr(p, "consumo_12m", None) or [])

    if len(consumo_12m_kwh) != 12:
        raise ValueError("consumo_12m debe contener 12 valores")

    consumo_12m_kwh = [float(x or 0.0) for x in consumo_12m_kwh]

    consumo_anual = consumo_anual_kwh(consumo_12m_kwh)

    cobertura_obj = normalizar_cobertura(
        getattr(p, "cobertura_obj", 1.0)
    )

    return consumo_anual, cobertura_obj

def _leer_modo_dimensionado(p: Datosproyecto):

    sf = getattr(p, "sistema_fv", {}) or {}

    modo_dimensionado = str(
        sf.get("modo_dimensionado", "auto")
    ).strip().lower()

    n_paneles_manual = None
    area_m2 = None
    factor_ocupacion = None

    if modo_dimensionado == "manual":

        try:
            n_paneles_manual = int(sf.get("n_paneles_manual"))

            if n_paneles_manual <= 0:
                raise ValueError

        except Exception:
            raise ValueError("n_paneles_manual inválido en modo manual")

    elif modo_dimensionado == "area":

        try:
            area_m2 = float(sf.get("area_disponible_m2"))
            factor_ocupacion = float(sf.get("factor_ocupacion", 0.75))
        except Exception:
            raise ValueError("Datos de área inválidos")

    return modo_dimensionado, n_paneles_manual, area_m2, factor_ocupacion

# ==========================================================
# Generador FV
# ==========================================================
def _dimensionar_generador(
    panel,
    modo_dimensionado,
    n_paneles_manual,
    consumo_anual,
    cobertura_obj,
    area_m2=None,
    factor_ocupacion=None
):

    energia_por_kwp_anual = 1500.0

    # =============================
    # MODO CONSUMO
    # =============================
    if modo_dimensionado == "consumo":

        kwp_objetivo = (consumo_anual * cobertura_obj) / energia_por_kwp_anual

    # =============================
    # MODO ÁREA
    # =============================
    elif modo_dimensionado == "area":

        if area_m2 is None:
            raise ValueError("Área no definida para modo area")

        area_util = area_m2 * (factor_ocupacion or 0.75)

        kwp_objetivo = area_util / 5  # regla m² → kWp

    # =============================
    # MODO MANUAL
    # =============================
    else:
        kwp_objetivo = None

    from electrical.paneles.entrada_panel import EntradaPaneles

    entrada_panel = EntradaPaneles(
        panel=panel,
        inversor=None,
        pdc_kw_objetivo=kwp_objetivo,
        t_min_c=10,
        t_oper_c=50,
        n_paneles_total=n_paneles_manual if modo_dimensionado == "manual" else None,
    )

    panel_sizing = dimensionar_paneles(entrada_panel)

    if not panel_sizing.ok:
        raise ValueError(f"Panel sizing inválido: {panel_sizing.errores}")

    kwp_req = float(panel_sizing.kwp_req)
    n_pan = int(panel_sizing.n_paneles)
    pdc = float(panel_sizing.pdc_kw)

    return kwp_req, n_pan, pdc

# ==========================================================
# INVERSOR (FIX)
# ==========================================================
from electrical.catalogos import get_inversor  # 👈 IMPORTANTE

def _seleccionar_inversor(pdc, dc_ac_obj, eq):

    resultado_inv = ejecutar_inversor_desde_sizing(
        pdc_kw=pdc,
        dc_ac_obj=dc_ac_obj,
        inversor_id_forzado=_inv_id(eq),
    )

    print("DEBUG resultado_inv:", resultado_inv)

    if not isinstance(resultado_inv, dict):
        raise ValueError(f"Formato inesperado en inversor: {resultado_inv}")

    # 🔥 VALIDACIÓN
    if "inversor_id" not in resultado_inv:
        raise ValueError(f"Resultado inválido sin inversor_id: {resultado_inv}")

    inversor_id = resultado_inv["inversor_id"]

    # 🔥 CONVERSIÓN A OBJETO REAL
    inversor = get_inversor(inversor_id)

    if inversor is None:
        raise ValueError(f"Inversor no encontrado en catálogo: {inversor_id}")

    kw_ac = float(resultado_inv.get("kw_ac", 0))
    n_inversores = int(resultado_inv.get("n_inversores", 1))

    if kw_ac <= 0:
        raise ValueError(f"kw_ac inválido: {kw_ac}")

    pac_total_kw = float(resultado_inv.get("kw_ac_total", kw_ac * n_inversores))

    return inversor, kw_ac, n_inversores, pac_total_kw
# ==========================================================
# API PRINCIPAL
# ==========================================================

def calcular_sizing_unificado(
    p: Datosproyecto,
) -> ResultadoSizing:

    panel, dc_ac_obj, eq = _leer_panel_y_config(p)

    consumo_anual, cobertura_obj = _leer_consumo_y_cobertura(p)

    modo_dimensionado, n_paneles_manual, area_m2, factor_ocupacion = _leer_modo_dimensionado(p)

    kwp_req, n_pan, pdc = _dimensionar_generador(
        panel,
        modo_dimensionado,
        n_paneles_manual,
        consumo_anual,
        cobertura_obj,
        area_m2,
        factor_ocupacion
    )

    # 🔥 FIX: ahora trae inversor
    inversor, kw_ac, n_inversores, pac_total_kw = _seleccionar_inversor(
        pdc,
        dc_ac_obj,
        eq
    )

    paneles_por_inversor = ceil(n_pan / n_inversores)

    energia_12m: List[MesEnergia] = []

    return ResultadoSizing(
        n_paneles=n_pan,
        kwp_dc=round(pdc, 3),
        pdc_kw=round(pdc, 3),

        kw_ac=pac_total_kw,
        n_inversores=n_inversores,
        paneles_por_inversor=paneles_por_inversor,

        inversor=inversor,   # 🔥 FIX FINAL

        energia_12m=energia_12m,
    )
