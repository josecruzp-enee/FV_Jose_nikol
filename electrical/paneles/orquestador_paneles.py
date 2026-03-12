from __future__ import annotations

from typing import List

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec

from .calculo_de_strings import calcular_strings_fv
from .entrada_panel import EntradaPaneles
from .resultado_paneles import ResultadoPaneles
from .validacion_strings import (
    validar_inversor,
    validar_panel,
    validar_parametros_generales,
)

# ==========================================================
# ORQUESTADOR DEL DOMINIO PANELES
# ==========================================================


def ejecutar_paneles(
    entrada: EntradaPaneles
) -> ResultadoPaneles:

    errores: List[str] = []
    warnings: List[str] = []

    panel: PanelSpec = entrada.panel
    inversor: InversorSpec = entrada.inversor

    n_paneles_total = entrada.n_paneles_total

    if n_paneles_total is None or n_paneles_total <= 0:

        return ResultadoPaneles(
            ok=False,
            topologia="desconocida",
            array=None,
            recomendacion=None,
            strings=[],
            warnings=[],
            errores=["n_paneles_total inválido"],
            meta={},
        )

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

        return ResultadoPaneles(
            ok=False,
            topologia="desconocida",
            array=None,
            recomendacion=None,
            strings=[],
            warnings=warnings,
            errores=errores,
            meta={},
        )

    # ------------------------------------------------------
    # CALCULO DE STRINGS
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

    return resultado


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# ejecutar_paneles(entrada: EntradaPaneles)
#
# devuelve:
#
# ResultadoPaneles
#
# Campos principales:
#
# ok : bool
# array : ArrayFV
# recomendacion : RecomendacionStrings
# strings : list[StringFV]
#
# warnings : list[str]
# errores : list[str]
#
# meta : dict
#
# Consumido por:
# core
#
# ==========================================================
