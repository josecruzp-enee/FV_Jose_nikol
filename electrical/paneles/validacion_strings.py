from __future__ import annotations

"""
VALIDACIÓN DEL DOMINIO PANELES — FV ENGINE
=========================================

Este módulo valida coherencia de:

    - PanelSpec
    - InversorSpec
    - Parámetros generales

NO ejecuta cálculos eléctricos.

----------------------------------------------------------
SALIDA

Todas las funciones retornan:

    ValidacionResultado

----------------------------------------------------------
REGLA

NO usar tuple
NO usar dict
SOLO dataclass
"""

from dataclasses import dataclass
from typing import List, Optional

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


# =========================================================
# RESULTADO DE VALIDACIÓN
# =========================================================

@dataclass(frozen=True)
class ValidacionResultado:
    ok: bool
    errores: List[str]
    warnings: List[str]


# =========================================================
# VALIDACIÓN PANEL
# =========================================================

def validar_panel(panel: PanelSpec) -> ValidacionResultado:

    errores: List[str] = []
    warnings: List[str] = []

    if panel.voc_v <= 0 or panel.vmp_v <= 0:
        errores.append("Panel inválido: Voc/Vmp deben ser > 0.")

    if panel.isc_a <= 0 or panel.imp_a <= 0:
        errores.append("Panel inválido: Isc/Imp deben ser > 0.")

    if panel.pmax_w <= 0:
        warnings.append("Panel: pmax_w <= 0 (revisar catálogo).")

    if panel.coef_voc_pct_c >= 0:
        warnings.append("Panel: coef_voc_pct_c normalmente es negativo.")

    if panel.coef_vmp_pct_c >= 0:
        warnings.append("Panel: coef_vmp_pct_c normalmente es negativo.")

    if panel.vmp_v > panel.voc_v:
        warnings.append("Panel: Vmp > Voc (posible error de datos).")

    return ValidacionResultado(
        ok=len(errores) == 0,
        errores=errores,
        warnings=warnings
    )


# =========================================================
# VALIDACIÓN INVERSOR
# =========================================================

def validar_inversor(inversor: InversorSpec) -> ValidacionResultado:

    errores: List[str] = []
    warnings: List[str] = []

    if inversor.vdc_max_v <= 0:
        errores.append("Inversor inválido: vdc_max_v <= 0.")

    if inversor.mppt_min_v <= 0 or inversor.mppt_max_v <= 0:
        errores.append("Inversor inválido: ventana MPPT inválida.")

    if inversor.mppt_min_v >= inversor.mppt_max_v:
        errores.append("Inversor inválido: mppt_min_v >= mppt_max_v.")

    if inversor.imppt_max_a <= 0:
        errores.append("Inversor inválido: imppt_max_a <= 0.")

    if inversor.n_mppt <= 0:
        errores.append("Inversor inválido: n_mppt <= 0.")

    if inversor.vdc_max_v < inversor.mppt_max_v:
        warnings.append("Inversor: vdc_max_v < mppt_max_v.")

    if inversor.kw_ac <= 0:
        warnings.append("Inversor: kw_ac <= 0.")

    return ValidacionResultado(
        ok=len(errores) == 0,
        errores=errores,
        warnings=warnings
    )


# =========================================================
# VALIDACIÓN PARÁMETROS GENERALES
# =========================================================

def validar_parametros_generales(
    n_paneles_total: int,
    t_min_c: float,
    t_oper_c: Optional[float] = None,
) -> ValidacionResultado:

    errores: List[str] = []
    warnings: List[str] = []

    if int(n_paneles_total) <= 0:
        errores.append("n_paneles_total inválido (<=0).")

    try:
        float(t_min_c)
    except Exception:
        errores.append("t_min_c inválido.")

    if t_oper_c is not None:
        try:
            float(t_oper_c)
        except Exception:
            errores.append("t_oper_c inválido.")

    return ValidacionResultado(
        ok=len(errores) == 0,
        errores=errores,
        warnings=warnings
    )

# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# FUNCIONES:
# ----------------------------------------------------------
# validar_panel(panel: PanelSpec)
# validar_inversor(inversor: InversorSpec)
# validar_parametros_generales(...)
#
#
# ----------------------------------------------------------
# ENTRADA
# ----------------------------------------------------------
#
# PanelSpec:
#   - voc_v
#   - vmp_v
#   - isc_a
#   - imp_a
#   - pmax_w
#   - coeficientes térmicos
#
# InversorSpec:
#   - vdc_max_v
#   - mppt_min_v
#   - mppt_max_v
#   - imppt_max_a
#   - n_mppt
#   - kw_ac
#
# Parámetros:
#   - n_paneles_total
#   - t_min_c
#   - t_oper_c
#
#
# ----------------------------------------------------------
# PROCESO
# ----------------------------------------------------------
#
# - valida coherencia de datos eléctricos
# - detecta errores críticos
# - genera advertencias técnicas
#
# NO realiza cálculos eléctricos
#
#
# ----------------------------------------------------------
# SALIDA
# ----------------------------------------------------------
#
# ValidacionResultado:
#
#   ok       → estado de validación
#   errores  → lista de errores críticos
#   warnings → advertencias
#
#
# ----------------------------------------------------------
# UBICACIÓN EN FLUJO
# ----------------------------------------------------------
#
# EntradaPaneles
#       ↓
# VALIDACIÓN (este módulo)
#       ↓
# dimensionado_paneles
#       ↓
# cálculo de strings
#
#
# ----------------------------------------------------------
# CONSUMIDO POR
# ----------------------------------------------------------
#
# electrical.paneles.orquestador_paneles
#
#
# ----------------------------------------------------------
# PRINCIPIO
# ----------------------------------------------------------
#
# Validar antes de calcular.
#
# ==========================================================
