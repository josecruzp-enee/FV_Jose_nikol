from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO PANELES
=====================================================

Este módulo coordina el cálculo completo del generador
fotovoltaico.

Responsabilidad:
    Coordinar motores del dominio paneles.

Este módulo NO implementa cálculos eléctricos complejos.

---------------------------------------------------------
FLUJO DEL DOMINIO
---------------------------------------------------------

EntradaPaneles
    ↓
validaciones
    ↓
dimensionado de paneles
    ↓
cálculo de strings
    ↓
resultado final del dominio


---------------------------------------------------------
ENTRADA
---------------------------------------------------------

entrada : EntradaPaneles

Contiene:

    panel : PanelSpec
    inversor : InversorSpec

    n_paneles_total : int
    n_inversores : int | None

    t_min_c : float
    t_oper_c : float

    dos_aguas : bool

    objetivo_dc_ac : float | None
    pdc_kw_objetivo : float | None


---------------------------------------------------------
SALIDA
---------------------------------------------------------

dict

{
    ok : bool

    errores : list[str]

    warnings : list[str]

    strings : list

    recomendacion : {...}

    bounds : {...}

    meta : {
        n_paneles_total
        pdc_kw
        n_inversores
    }
}
"""

from typing import Dict, List

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec

from .calculo_de_strings import calcular_strings_fv
from .dimensionado_paneles import dimensionar_paneles
from .entrada_panel import EntradaPaneles

from .validacion_strings import (
    validar_panel,
    validar_inversor,
    validar_parametros_generales,
)

# ==========================================================
# DEBUG STREAMLIT (solo si existe)
# ==========================================================

try:
    import streamlit as st
    DEBUG_UI = True
except Exception:
    DEBUG_UI = False


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================

from typing import Dict, List

from .contrato import ResultadoPaneles, ArrayFV, StringFV


def ejecutar_paneles(
    entrada
) -> ResultadoPaneles:

    errores: List[str] = []
    warnings: List[str] = []

    panel = entrada.panel
    inversor = entrada.inversor

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
        entrada.n_paneles_total,
        entrada.t_min_c,
        entrada.t_oper_c,
    )

    errores += e
    warnings += w

    if errores:
        return ResultadoPaneles(
            ok=False,
            array=ArrayFV(pdc_kw=0.0, n_strings=0),
            strings=[]
        )

    # ------------------------------------------------------
    # DIMENSIONADO DE PANELES
    # ------------------------------------------------------

    dim = dimensionar_paneles(entrada)

    if not dim.ok:
        return ResultadoPaneles(
            ok=False,
            array=ArrayFV(pdc_kw=0.0, n_strings=0),
            strings=[]
        )

    n_paneles_total = dim.n_paneles

    if n_paneles_total <= 0:
        return ResultadoPaneles(
            ok=False,
            array=ArrayFV(pdc_kw=0.0, n_strings=0),
            strings=[]
        )

    # ------------------------------------------------------
    # PARÁMETROS DE CÁLCULO
    # ------------------------------------------------------

    n_inversores = max(1, int(entrada.n_inversores or 1))

    # ------------------------------------------------------
    # CÁLCULO DE STRINGS
    # ------------------------------------------------------

    resultado = calcular_strings_fv(

        n_paneles_total=n_paneles_total,
        panel=panel,
        inversor=inversor,
        n_inversores=n_inversores,
        t_min_c=float(entrada.t_min_c),
        dos_aguas=bool(entrada.dos_aguas),
        objetivo_dc_ac=entrada.objetivo_dc_ac,
        pdc_kw_objetivo=entrada.pdc_kw_objetivo,
        t_oper_c=entrada.t_oper_c,
    )

    # ------------------------------------------------------
    # NORMALIZAR RESULTADO
    # ------------------------------------------------------

    resultado.setdefault("ok", False)
    resultado.setdefault("errores", [])
    resultado.setdefault("warnings", [])

    resultado["warnings"] = warnings + list(resultado.get("warnings", []))

    resultado.setdefault("meta", {})

    resultado["meta"]["n_paneles_total"] = n_paneles_total
    resultado["meta"]["pdc_kw"] = dim.pdc_kw
    resultado["meta"]["n_inversores"] = n_inversores

    # ------------------------------------------------------
    # SI HUBO ERROR EN STRINGS
    # ------------------------------------------------------

    if not resultado.get("ok", False):
        return ResultadoPaneles(
            ok=False,
            array=ArrayFV(pdc_kw=0.0, n_strings=0),
            strings=[]
        )

    # ------------------------------------------------------
    # CONVERTIR STRINGS → OBJETO
    # ------------------------------------------------------

    strings_obj = []

    for s in resultado.get("strings", []):

        strings_obj.append(
            StringFV(
                id=s["id"],
                inversor=s["inversor"],
                mppt=s["mppt"],
                n_series=s["n_series"],
                vmp_string_v=s["vmp_string_v"],
                voc_string_v=s["voc_frio_string_v"],
                imp_string_a=s["imp_string_a"],
                isc_string_a=s["isc_string_a"],
            )
        )

    # ------------------------------------------------------
    # ARRAY
    # ------------------------------------------------------

    array = ArrayFV(
        pdc_kw=resultado.get("meta", {}).get("pdc_kw", 0.0),
        n_strings=resultado.get("n_strings_total", len(strings_obj)),
    )

    # ------------------------------------------------------
    # SALIDA FINAL (OBJETO)
    # ------------------------------------------------------

    return ResultadoPaneles(
        ok=True,
        array=array,
        strings=strings_obj,
    )
# ==========================================================
# SALIDA DEL DOMINIO
# ==========================================================

"""
ejecutar_paneles(entrada: EntradaPaneles) -> Dict

Consumido por:

    core.aplicacion.orquestador_estudio
"""
