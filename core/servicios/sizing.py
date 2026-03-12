"""
Servicio de sizing FV.

FRONTERA DEL MÓDULO
===================

Entrada:
    Datosproyecto

Salida:
    ResultadoSizing

Este módulo:
    - calcula número de paneles
    - calcula potencia DC instalada
    - selecciona inversor
    - divide arreglo por inversor

Este módulo NO:
    - calcula strings
    - calcula corrientes
    - calcula NEC
"""

from __future__ import annotations

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
# API pública — Servicio de sizing
# ==========================================================

def calcular_sizing_unificado(
    p: Datosproyecto,
) -> ResultadoSizing:
    """
    API pública del servicio de sizing.

    Entrada:
        p : Datosproyecto

    Salida:
        ResultadoSizing

    Consumido por:
        core.aplicacion.orquestador_estudio
    """

    # ======================================================
    # Equipos
    # ======================================================

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

    # ======================================================
    # Consumo
    # ======================================================

    consumo_12m_kwh = list(getattr(p, "consumo_12m", None) or [])

    if len(consumo_12m_kwh) != 12:
        raise ValueError("consumo_12m debe contener 12 valores")

    consumo_12m_kwh = [float(x or 0.0) for x in consumo_12m_kwh]

    cobertura_obj = normalizar_cobertura(
        getattr(p, "cobertura_obj", 1.0)
    )

    # ======================================================
    # Modo dimensionamiento
    # ======================================================

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

    # ======================================================
    # PANEL SIZING
    # ======================================================

    panel_sizing = dimensionar_paneles(

        consumo_12m_kwh=consumo_12m_kwh,
        cobertura_obj=cobertura_obj,
        panel_w=panel_w,
        modo=modo_dimensionado,
        n_paneles_manual=n_paneles_manual,
    )

    if not panel_sizing.ok:
        raise ValueError(f"Panel sizing inválido: {panel_sizing.errores}")

    kwp_req = float(panel_sizing.kwp_req)
    n_pan = int(panel_sizing.n_paneles)
    pdc = float(panel_sizing.pdc_kw)

    if n_pan <= 0 or pdc <= 0:
        raise ValueError("Sizing resultó en sistema inválido")

    # ======================================================
    # INVERSOR
    # ======================================================

    resultado_inv = ejecutar_inversor_desde_sizing(

        pdc_kw=pdc,
        dc_ac_obj=dc_ac_obj,
        inversor_id_forzado=_inv_id(eq),
    )

    kw_ac = float(resultado_inv["kw_ac"])

    n_inversores = int(
        resultado_inv.get("n_inversores", 1)
    )

    pac_total_kw = kw_ac * n_inversores

    # ======================================================
    # DIVISIÓN DEL ARREGLO
    # ======================================================

    paneles_por_inversor = ceil(
        n_pan / n_inversores
    )

    # ======================================================
    # Energía inicial
    # ======================================================

    energia_12m: List[MesEnergia] = []

    # ======================================================
    # Resultado final
    # ======================================================

    return ResultadoSizing(

        n_paneles=n_pan,

        kwp_dc=round(pdc, 3),

        pdc_kw=round(pdc, 3),

        kw_ac=pac_total_kw,

        n_inversores=n_inversores,

        paneles_por_inversor=paneles_por_inversor,

        energia_12m=energia_12m,
    )


# ==========================================================
# SALIDAS DEL MÓDULO
# ==========================================================
#
# calcular_sizing_unificado()
#
# devuelve:
#
# ResultadoSizing
#
# Campos principales:
#   n_paneles
#   pdc_kw
#   kw_ac
#   n_inversores
#   paneles_por_inversor
#   energia_12m
#
# Consumido por:
# core.aplicacion.orquestador_estudio
#
# ==========================================================
