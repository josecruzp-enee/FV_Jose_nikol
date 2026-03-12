from __future__ import annotations
from typing import Dict, List

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec

from .calculo_de_strings import calcular_strings_fv
from .entrada_panel import EntradaPaneles
from .validacion_strings import validar_inversor, validar_panel, validar_parametros_generales

# ==========================================================
# ORQUESTADOR DEL DOMINIO PANELES
# ==========================================================

def ejecutar_paneles(
    entrada: EntradaPaneles
) -> Dict:

    errores: List[str] = []
    warnings: List[str] = []

    panel: PanelSpec = entrada.panel
    inversor: InversorSpec = entrada.inversor

    n_paneles_total = entrada.n_paneles_total

    if n_paneles_total is None or n_paneles_total <= 0:
        return {
            "ok": False,
            "errores": ["n_paneles_total inválido"],
            "warnings": []
        }

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    e, w = validar_panel(panel)
    errores += e
    warnings += w

    e, w = validar_inversor(inversor)
    errores += e
    warnings += w

    e, w = validar_parametros_generales(
        n_paneles_total,
        entrada.t_min_c,
        entrada.t_oper_c
    )

    errores += e
    warnings += w

    if errores:

        return {
            "ok": False,
            "errores": errores,
            "warnings": warnings
        }

    # ------------------------------------------------------
    # CALCULO STRINGS
    # ------------------------------------------------------

    resultado = calcular_strings_fv(

        n_paneles_total=n_paneles_total,
        panel=panel,
        inversor=inversor,
        t_min_c=float(entrada.t_min_c),
        dos_aguas=bool(entrada.dos_aguas),
        objetivo_dc_ac=entrada.objetivo_dc_ac,
        pdc_kw_objetivo=entrada.pdc_kw_objetivo,
        t_oper_c=entrada.t_oper_c,
    )

    resultado.setdefault("ok", False)
    resultado.setdefault("errores", [])
    resultado.setdefault("warnings", [])

    return resultado


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# ejecutar_paneles(entrada: EntradaPaneles)
#
# devuelve:
#
# ok : bool
# errores : list[str]
# warnings : list[str]
#
# strings : list
#
# recomendacion:
#   n_series
#   n_strings_total
#   vmp_string_v
#   voc_string_v
#   imp_array_a
#   isc_array_total_a
#
# bounds:
#   n_min
#   n_max
#
# meta:
#   n_paneles_total
#
# Consumido por:
# core
#
# ==========================================================
