from __future__ import annotations

"""
Servicio de sizing FV (REFORMADO).
"""

from typing import Any, Dict, Optional, List
from math import ceil

from core.dominio.modelo import Datosproyecto
from core.dominio.contrato import ResultadoSizing, MesEnergia

from core.servicios.consumo import (
    consumo_anual_kwh,
    normalizar_cobertura,
)

from electrical.catalogos import get_panel, get_inversor
from electrical.inversor.orquestador_inversor import ejecutar_inversor_desde_sizing
from electrical.paneles.dimensionado_paneles import dimensionar_paneles


# ==========================================================
# HELPERS
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
# PANEL + CONFIG
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
        1.0,
        2.0,
    )

    return panel, dc_ac_obj, eq


# ==========================================================
# CONSUMO
# ==========================================================

def _leer_consumo(p: Datosproyecto):

    consumo_12m = list(getattr(p, "consumo_12m", []) or [])

    if len(consumo_12m) != 12:
        raise ValueError("consumo_12m debe tener 12 valores")

    consumo_12m = [float(x or 0.0) for x in consumo_12m]

    consumo_anual = consumo_anual_kwh(consumo_12m)

    return consumo_anual


# ==========================================================
# NUEVO: LECTURA DE SIZING_INPUT
# ==========================================================

def _leer_sizing_input(p: Datosproyecto):

    sf = getattr(p, "sistema_fv", {}) or {}
    si = sf.get("sizing_input", {}) or {}

    modo = str(si.get("modo", "consumo")).strip().lower()
    valor = si.get("valor", None)

    if valor is None:
        raise ValueError("sizing_input sin valor")

    return modo, valor


# ==========================================================
# GENERADOR FV
# ==========================================================

def _dimensionar_generador(panel, modo, valor, consumo_anual):

    energia_por_kwp_anual = 1500.0

    # =============================
    # CONSUMO
    # =============================
    if modo == "consumo":

        cobertura = _clamp(float(valor) / 100.0, 0.1, 2.0)
        kwp_obj = (consumo_anual * cobertura) / energia_por_kwp_anual

        n_paneles_manual = None

    # =============================
    # ÁREA
    # =============================
    elif modo == "area":

        area = float(valor)
        area_util = area * 0.75
        kwp_obj = area_util / 5.0

        n_paneles_manual = None

    # =============================
    # POTENCIA
    # =============================
    elif modo == "potencia":

        kwp_obj = float(valor)
        n_paneles_manual = None

    # =============================
    # MANUAL
    # =============================
    elif modo == "manual":

        n_paneles_manual = int(valor)

        if n_paneles_manual <= 0:
            raise ValueError("Número de paneles inválido")

        kwp_obj = None

    else:
        raise ValueError(f"Modo inválido: {modo}")

    # =============================
    # MOTOR DE PANELES
    # =============================
    from electrical.paneles.entrada_panel import EntradaPaneles

    entrada = EntradaPaneles(
        panel=panel,
        inversor=None,
        pdc_kw_objetivo=kwp_obj,
        t_min_c=10,
        t_oper_c=50,
        n_paneles_total=n_paneles_manual,
    )

    res = dimensionar_paneles(entrada)

    if not res.ok:
        raise ValueError(res.errores)

    return res.n_paneles, res.pdc_kw


# ==========================================================
# INVERSOR
# ==========================================================

def _seleccionar_inversor(pdc, dc_ac_obj, eq):

    resultado = ejecutar_inversor_desde_sizing(
        pdc_kw=pdc,
        dc_ac_obj=dc_ac_obj,
        inversor_id_forzado=_inv_id(eq),
    )

    inv_id = resultado["inversor_id"]
    inv = get_inversor(inv_id)

    kw_ac = float(resultado.get("kw_ac", 0))
    n_inv = int(resultado.get("n_inversores", 1))

    if kw_ac <= 0:
        raise ValueError("kw_ac inválido")

    pac_total = float(resultado.get("kw_ac_total", kw_ac * n_inv))

    dc_ac_ratio = pdc / pac_total

    if not (1.1 <= dc_ac_ratio <= 1.3):
        raise ValueError(f"DC/AC fuera de rango: {dc_ac_ratio:.2f}")

    return inv, kw_ac, n_inv, pac_total, resultado.get("sugerencias", [])


# ==========================================================
# API PRINCIPAL
# ==========================================================

def calcular_sizing_unificado(p: Datosproyecto) -> ResultadoSizing:

    panel, dc_ac_obj, eq = _leer_panel_y_config(p)

    consumo_anual = _leer_consumo(p)

    modo, valor = _leer_sizing_input(p)

    n_paneles, pdc = _dimensionar_generador(
        panel,
        modo,
        valor,
        consumo_anual
    )

    inv, kw_ac, n_inv, pac_total, sugerencias = _seleccionar_inversor(
        pdc,
        dc_ac_obj,
        eq
    )

    eq["sugerencias_inversor"] = sugerencias

    paneles_por_inversor = ceil(n_paneles / n_inv)

    dc_ac_ratio = pdc / pac_total

    energia_12m: List[MesEnergia] = []

    return ResultadoSizing(
        n_paneles=n_paneles,
        kwp_dc=round(pdc, 3),
        pdc_kw=round(pdc, 3),

        kw_ac=pac_total,
        kw_ac_total=pac_total,
        n_inversores=n_inv,
        paneles_por_inversor=paneles_por_inversor,

        inversor=inv,
        dc_ac_ratio=round(dc_ac_ratio, 3),

        energia_12m=energia_12m,
    )
