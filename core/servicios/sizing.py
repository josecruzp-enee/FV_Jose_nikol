from __future__ import annotations

"""
Servicio de sizing FV — VERSIÓN ALINEADA FINAL
"""

from typing import Any, Dict, Optional, List
from math import ceil

from core.dominio.modelo import Datosproyecto
from core.dominio.contrato import ResultadoSizing, MesEnergia

from core.servicios.consumo import consumo_anual_kwh

from electrical.catalogos import get_panel, get_inversor
from electrical.inversor.orquestador_inversor import ejecutar_inversor_desde_sizing


# ==========================================================
# HELPERS
# ==========================================================

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def _leer_equipos(p):

    eq = getattr(p, "equipos", None)

    if eq is None:
        raise ValueError("p.equipos no definido")

    if hasattr(eq, "panel_id") and hasattr(eq, "inversor_id"):
        return eq

    if isinstance(eq, dict):
        panel_id = eq.get("panel_id")
        inversor_id = eq.get("inversor_id")

        if not panel_id or not inversor_id:
            raise ValueError("Datos incompletos en p.equipos")

        return type("EquiposTmp", (), {
            "panel_id": panel_id,
            "inversor_id": inversor_id,
        })()

    raise ValueError("Formato inválido en p.equipos")


def _panel_id(eq) -> str:
    pid = str(getattr(eq, "panel_id", "")).strip()

    if not pid:
        raise ValueError("panel_id no definido")

    return pid


def _inv_id(eq) -> Optional[str]:
    v = getattr(eq, "inversor_id", None)
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
        raise ValueError("Panel no encontrado")

    panel_w = float(getattr(panel, "pmax_w", 0.0))

    if panel_w <= 0:
        raise ValueError("Potencia de panel inválida")

    dc_ac_obj = _clamp(
        float(getattr(eq, "sobredimension_dc_ac", 1.20)),
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

    return consumo_anual_kwh(consumo_12m)


# ==========================================================
# SIZING INPUT
# ==========================================================

def _leer_sizing_input(p: Datosproyecto):

    sf = getattr(p, "sistema_fv", {}) or {}

    # 🔥 NUEVO MODELO (YA NO USA sizing_input)
    modo = sf.get("modo")
    valor = sf.get("valor")

    # ======================================================
    # VALIDACIONES
    # ======================================================
    if not modo:
        raise ValueError(f"sistema_fv sin modo: {sf}")

    if modo != "multizona" and (valor is None or float(valor) <= 0):
        raise ValueError(f"sistema_fv sin valor válido: {sf}")

    return modo, valor
# ==========================================================
# GENERADOR (NO MULTIZONA)
# ==========================================================

def _dimensionar_generador(panel, modo, valor, consumo_anual):

    energia_por_kwp_anual = 1500.0

    if modo == "cobertura":

        cobertura = _clamp(float(valor) / 100.0, 0.1, 2.0)
        kwp_obj = (consumo_anual * cobertura) / energia_por_kwp_anual

    elif modo == "area":

        area = float(valor)
        area_util = area * 0.75
        kwp_obj = area_util / 5.0

    elif modo == "kw_objetivo":

        kwp_obj = float(valor)

    elif modo == "paneles":

        n_paneles = int(valor)

        if n_paneles <= 0:
            raise ValueError("Número de paneles inválido")

        pdc_kw = (n_paneles * panel.pmax_w) / 1000
        return n_paneles, pdc_kw

    else:
        raise ValueError(f"Modo inválido: {modo}")

    n_paneles = int(ceil((kwp_obj * 1000) / panel.pmax_w))
    pdc_kw = (n_paneles * panel.pmax_w) / 1000

    return n_paneles, pdc_kw


# ==========================================================
# MULTIZONA
# ==========================================================

def _dimensionar_por_zonas(panel, zonas):

    total_paneles = 0
    total_pdc = 0

    for i, z in enumerate(zonas):

        if "n_paneles" in z:

            n_paneles = int(z.get("n_paneles") or 0)

            if n_paneles <= 0:
                raise ValueError(f"Zona {i+1}: paneles inválidos")

            pdc_kw = (n_paneles * panel.pmax_w) / 1000

        elif "area" in z:

            area = float(z.get("area") or 0.0)

            if area <= 0:
                raise ValueError(f"Zona {i+1}: área inválida")

            area_util = area * 0.75
            kwp_obj = area_util / 5.0

            n_paneles = int(ceil((kwp_obj * 1000) / panel.pmax_w))
            pdc_kw = (n_paneles * panel.pmax_w) / 1000

        else:
            raise ValueError(f"Zona {i+1}: configuración inválida")

        total_paneles += n_paneles
        total_pdc += pdc_kw

    if total_paneles <= 0:
        raise ValueError("Multizona inválido")

    return total_paneles, total_pdc


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
    pac_total = float(resultado.get("kw_ac_total", kw_ac * n_inv))

    if kw_ac <= 0:
        raise ValueError("kw_ac inválido")

    return inv, kw_ac, n_inv, pac_total


# ==========================================================
# API PRINCIPAL
# ==========================================================

def calcular_sizing_unificado(p: Datosproyecto) -> ResultadoSizing:

    panel, dc_ac_obj, eq = _leer_panel_y_config(p)
    consumo_anual = _leer_consumo(p)

    sf = getattr(p, "sistema_fv", {}) or {}

    modo = sf.get("modo")

    # ======================================================
    # MULTIZONA
    # ======================================================
    if modo == "multizona":

        zonas = sf.get("zonas", [])

        if not zonas:
            raise ValueError("Multizona sin zonas")

        n_paneles, pdc = _dimensionar_por_zonas(panel, zonas)

    # ======================================================
    # NORMAL
    # ======================================================
    else:

        modo, valor = _leer_sizing_input(p)

        n_paneles, pdc = _dimensionar_generador(
            panel,
            modo,
            valor,
            consumo_anual
        )

    # ======================================================
    # INVERSOR
    # ======================================================
    inv, kw_ac, n_inv, pac_total = _seleccionar_inversor(
        pdc,
        dc_ac_obj,
        eq
    )

    paneles_por_inversor = ceil(n_paneles / n_inv)
    dc_ac_ratio = pdc / pac_total

    energia_12m: List[MesEnergia] = []

    return ResultadoSizing(
        n_paneles=n_paneles,
        kwp_dc=round(pdc, 3),
        pdc_kw=round(pdc, 3),

        kw_ac=kw_ac, 
        kw_ac_total=pac_total, 
        n_inversores=n_inv,
        paneles_por_inversor=paneles_por_inversor,

        inversor=inv,
        panel=panel,
        dc_ac_ratio=round(dc_ac_ratio, 3),

        energia_12m=energia_12m,
    )
