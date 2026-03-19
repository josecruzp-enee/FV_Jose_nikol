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

from typing import List, Dict

from .contrato import (
    ResultadoPaneles,
    ArrayFV,
    StringFV,
    RecomendacionStrings
)


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
            topologia="desconocida",
            array=ArrayFV(
                potencia_dc_w=0.0,
                vdc_nom=0.0,
                idc_nom=0.0,
                voc_frio_array_v=0.0,
                n_strings_total=0,
                n_paneles_total=0,
                strings_por_mppt=0,
                n_mppt=0,
                p_panel_w=0.0,
            ),
            recomendacion=RecomendacionStrings(
                n_series=0,
                n_strings_total=0,
                strings_por_mppt=0,
                vmp_string_v=0.0,
                vmp_stc_string_v=0.0,
                voc_frio_string_v=0.0,
            ),
            strings=[],
            warnings=warnings,
            errores=errores,
            meta={},
        )

    # ------------------------------------------------------
    # DIMENSIONADO
    # ------------------------------------------------------

    dim = dimensionar_paneles(entrada)

    if not dim.ok:
        return ResultadoPaneles(
            ok=False,
            topologia="desconocida",
            array=ArrayFV(
                potencia_dc_w=0.0,
                vdc_nom=0.0,
                idc_nom=0.0,
                voc_frio_array_v=0.0,
                n_strings_total=0,
                n_paneles_total=0,
                strings_por_mppt=0,
                n_mppt=0,
                p_panel_w=0.0,
            ),
            recomendacion=RecomendacionStrings(
                n_series=0,
                n_strings_total=0,
                strings_por_mppt=0,
                vmp_string_v=0.0,
                vmp_stc_string_v=0.0,
                voc_frio_string_v=0.0,
            ),
            strings=[],
            warnings=warnings,
            errores=dim.errores,
            meta={},
        )

    n_paneles_total = dim.n_paneles

    if n_paneles_total <= 0:
        return ResultadoPaneles(
            ok=False,
            topologia="desconocida",
            array=ArrayFV(
                potencia_dc_w=0.0,
                vdc_nom=0.0,
                idc_nom=0.0,
                voc_frio_array_v=0.0,
                n_strings_total=0,
                n_paneles_total=0,
                strings_por_mppt=0,
                n_mppt=0,
                p_panel_w=0.0,
            ),
            recomendacion=RecomendacionStrings(
                n_series=0,
                n_strings_total=0,
                strings_por_mppt=0,
                vmp_string_v=0.0,
                vmp_stc_string_v=0.0,
                voc_frio_string_v=0.0,
            ),
            strings=[],
            warnings=warnings,
            errores=["Número de paneles inválido"],
            meta={},
        )

    # ------------------------------------------------------
    # CÁLCULO STRINGS
    # ------------------------------------------------------

    n_inversores = max(1, int(entrada.n_inversores or 1))

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

    resultado.setdefault("ok", False)
    resultado.setdefault("errores", [])
    resultado.setdefault("warnings", [])

    resultado["warnings"] = warnings + list(resultado.get("warnings", []))

    resultado.setdefault("meta", {})
    resultado["meta"]["n_paneles_total"] = n_paneles_total
    resultado["meta"]["pdc_kw"] = dim.pdc_kw
    resultado["meta"]["n_inversores"] = n_inversores

    # ------------------------------------------------------
    # ERROR EN STRINGS
    # ------------------------------------------------------

    if not resultado.get("ok", False):
        return ResultadoPaneles(
            ok=False,
            topologia="desconocida",
            array=ArrayFV(
                potencia_dc_w=0.0,
                vdc_nom=0.0,
                idc_nom=0.0,
                voc_frio_array_v=0.0,
                n_strings_total=0,
                n_paneles_total=0,
                strings_por_mppt=0,
                n_mppt=0,
                p_panel_w=0.0,
            ),
            recomendacion=RecomendacionStrings(
                n_series=0,
                n_strings_total=0,
                strings_por_mppt=0,
                vmp_string_v=0.0,
                vmp_stc_string_v=0.0,
                voc_frio_string_v=0.0,
            ),
            strings=[],
            warnings=resultado.get("warnings", []),
            errores=resultado.get("errores", []),
            meta=resultado.get("meta", {}),
        )

    # ------------------------------------------------------
    # ARRAY
    # ------------------------------------------------------

    meta = resultado.get("meta", {})

    array = ArrayFV(
        potencia_dc_w=meta.get("pdc_kw", 0.0) * 1000.0,
        vdc_nom=resultado.get("vdc_nom", 0.0),
        idc_nom=resultado.get("idc_nom", 0.0),
        voc_frio_array_v=resultado.get("voc_frio_array_v", 0.0),
        n_strings_total=resultado.get("n_strings_total", 0),
        n_paneles_total=meta.get("n_paneles_total", 0),
        strings_por_mppt=resultado.get("strings_por_mppt", 0),
        n_mppt=resultado.get("n_mppt", 0),
        p_panel_w=panel.pmax_w,
    )

    # ------------------------------------------------------
    # RECOMENDACIÓN
    # ------------------------------------------------------

    rec = resultado.get("recomendacion", {})

    recomendacion = RecomendacionStrings(
        n_series=rec.get("n_series", 0),
        n_strings_total=rec.get("n_strings_total", 0),
        strings_por_mppt=rec.get("strings_por_mppt", 0),
        vmp_string_v=rec.get("vmp_string_v", 0.0),
        vmp_stc_string_v=rec.get("vmp_stc_string_v", 0.0),
        voc_frio_string_v=rec.get("voc_frio_string_v", 0.0),
    )

    # ------------------------------------------------------
    # STRINGS
    # ------------------------------------------------------

    strings_obj = []

    for s in resultado.get("strings", []):

        strings_obj.append(
            StringFV(
                mppt=s["mppt"],
                n_series=s["n_series"],
                n_strings=s.get("n_strings", 1),
                vmp_string_v=s["vmp_string_v"],
                voc_frio_string_v=s["voc_frio_string_v"],
                imp_string_a=s["imp_string_a"],
                isc_string_a=s["isc_string_a"],
                i_mppt_a=s.get("i_mppt_a", 0.0),
                isc_mppt_a=s.get("isc_mppt_a", 0.0),
                imax_pv_a=s.get("imax_pv_a", 0.0),
                idesign_cont_a=s.get("idesign_cont_a", 0.0),
            )
        )

    # ------------------------------------------------------
    # SALIDA FINAL
    # ------------------------------------------------------

    return ResultadoPaneles(
        ok=True,
        topologia=resultado.get("topologia", "desconocida"),
        array=array,
        recomendacion=recomendacion,
        strings=strings_obj,
        warnings=resultado.get("warnings", []),
        errores=resultado.get("errores", []),
        meta=meta,
    )
# ==========================================================
# SALIDA DEL DOMINIO
# ==========================================================

"""
ejecutar_paneles(entrada: EntradaPaneles) -> Dict

Consumido por:

    core.aplicacion.orquestador_estudio
"""
