"""
Dominio INVERSOR (selección y dimensionamiento AC).

FRONTERA DEL MÓDULO
===================

Entrada:
    pdc_kw
    dc_ac_obj
    inversor_id_forzado (opcional)

Salida:
    Dict con configuración de inversores

Responsabilidad:
    - seleccionar inversor
    - calcular cantidad de inversores
    - calcular potencia AC total

Este módulo NO:
    - calcula paneles
    - calcula strings
    - calcula corrientes
    - calcula NEC
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from math import ceil

from electrical.catalogos import get_inversor, ids_inversores


# ======================================================
# Helper cálculo cantidad de inversores
# ======================================================

def calcular_cantidad_inversores(
    pdc_kw: float,
    pac_inversor_kw: float,
    dc_ac_obj: float,
) -> Dict[str, float]:
    """
    Calcula número de inversores necesarios.

    Entrada:
        pdc_kw
        pac_inversor_kw
        dc_ac_obj

    Salida:
        dict con:
            n_inversores
            kw_ac
            kw_ac_total
            ratio_real
            kw_ac_obj
    """

    pac_obj = pdc_kw / dc_ac_obj

    n_inversores = ceil(pac_obj / pac_inversor_kw)

    pac_total = n_inversores * pac_inversor_kw

    ratio_real = pdc_kw / pac_total

    return {
        "n_inversores": n_inversores,
        "kw_ac": pac_inversor_kw,
        "kw_ac_total": pac_total,
        "ratio_real": ratio_real,
        "kw_ac_obj": pac_obj,
    }


# ======================================================
# ORQUESTADOR DEL DOMINIO INVERSOR
# ======================================================

def ejecutar_inversor_desde_sizing(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    inversor_id_forzado: Optional[str] = None,
) -> Dict[str, Any]:
    """
    API pública del dominio inversor.

    Entrada:
        pdc_kw
        dc_ac_obj
        inversor_id_forzado (opcional)

    Salida:
        Dict:
            inversor_id
            n_inversores
            kw_ac
            kw_ac_total
            ratio_real
            kw_ac_obj

    Consumido por:
        core.servicios.sizing
    """

    if pdc_kw <= 0:
        raise ValueError("pdc_kw inválido")

    if dc_ac_obj <= 0:
        raise ValueError("dc_ac_obj inválido")

    # --------------------------------------------------
    # INVERSOR FORZADO (modo manual)
    # --------------------------------------------------

    if inversor_id_forzado:

        inv = get_inversor(inversor_id_forzado)

        if inv is None:
            raise ValueError("Inversor forzado no encontrado")

        pac = float(inv.kw_ac)

        calc = calcular_cantidad_inversores(
            pdc_kw=pdc_kw,
            pac_inversor_kw=pac,
            dc_ac_obj=dc_ac_obj,
        )

        return {
            "inversor_id": inversor_id_forzado,
            **calc,
        }

    # --------------------------------------------------
    # SELECCIÓN AUTOMÁTICA
    # --------------------------------------------------

    mejor_total = None
    mejor_resultado = None
    mejor_id = None

    for iid in ids_inversores():

        inv = get_inversor(iid)

        if inv is None:
            continue

        pac = float(inv.kw_ac)

        if pac <= 0:
            continue

        calc = calcular_cantidad_inversores(
            pdc_kw=pdc_kw,
            pac_inversor_kw=pac,
            dc_ac_obj=dc_ac_obj,
        )

        pac_total = calc["kw_ac_total"]

        if mejor_total is None or pac_total < mejor_total:

            mejor_total = pac_total
            mejor_resultado = calc
            mejor_id = iid

    if mejor_resultado is None:
        raise RuntimeError("No se pudo seleccionar un inversor válido")

    return {
        "inversor_id": mejor_id,
        **mejor_resultado,
    }


# ======================================================
# SALIDAS DEL MÓDULO
# ======================================================
#
# ejecutar_inversor_desde_sizing()
#
# devuelve:
#
# {
#   inversor_id
#   n_inversores
#   kw_ac
#   kw_ac_total
#   ratio_real
#   kw_ac_obj
# }
#
# Consumido por:
# core.servicios.sizing
#
# ======================================================
