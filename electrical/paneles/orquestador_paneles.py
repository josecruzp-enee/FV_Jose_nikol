from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO PANELES — VERSION FINAL
==============================================

Coordina:

    EntradaPaneles
        ↓
    validaciones
        ↓
    dimensionado
        ↓
    cálculo de strings
        ↓
    ResultadoPaneles (TIPADO)

REGLA:
    - NO dict
    - NO get
    - NO lógica eléctrica
    - SOLO orquestación
"""

from typing import List

from .entrada_panel import EntradaPaneles
from .dimensionado_paneles import dimensionar_paneles
from .calculo_de_strings import calcular_strings_fv

from .validacion_strings import (
    validar_panel,
    validar_inversor,
    validar_parametros_generales,
)

from .resultado_paneles import (
    ResultadoPaneles,
    ArrayFV,
    StringFV,
    RecomendacionStrings,
)


# =========================================================
# HELPERS
# =========================================================

def _resultado_error(errores: List[str], warnings: List[str]) -> ResultadoPaneles:

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


# =========================================================
# ORQUESTADOR PRINCIPAL
# =========================================================

def ejecutar_paneles(entrada: EntradaPaneles) -> ResultadoPaneles:

    errores: List[str] = []
    warnings: List[str] = []

    panel = entrada.panel
    inversor = entrada.inversor

    # ======================================================
    # VALIDACIONES
    # ======================================================

    val = validar_panel(panel)
    errores += val.errores
    warnings += val.warnings

    val = validar_inversor(inversor)
    errores += val.errores
    warnings += val.warnings

    val = validar_parametros_generales(
        entrada.n_paneles_total,
        entrada.t_min_c,
        entrada.t_oper_c,
    )
    errores += val.errores
    warnings += val.warnings

    if errores:
        return _resultado_error(errores, warnings)

    # ======================================================
    # DIMENSIONADO
    # ======================================================

    dim = dimensionar_paneles(entrada)

    if not dim.ok:
        return _resultado_error(dim.errores, warnings)

    if dim.n_paneles <= 0:
        return _resultado_error(["Número de paneles inválido"], warnings)

    # ======================================================
    # STRINGS
    # ======================================================

    n_inversores = max(1, int(entrada.n_inversores or 1))

    strings_res = calcular_strings_fv(
        n_paneles_total=dim.n_paneles,
        panel=panel,
        inversor=inversor,
        n_inversores=n_inversores,
        t_min_c=float(entrada.t_min_c),
        t_oper_c=entrada.t_oper_c,
        dos_aguas=entrada.dos_aguas,
        objetivo_dc_ac=entrada.objetivo_dc_ac,
        pdc_kw_objetivo=entrada.pdc_kw_objetivo,
    )

    warnings += strings_res.warnings

    if not strings_res.ok:
        return _resultado_error(strings_res.errores, warnings)

    # ======================================================
    # ARRAY FV
    # ======================================================

    array = ArrayFV(
        potencia_dc_w=dim.pdc_kw * 1000.0,
        vdc_nom=strings_res.recomendacion.vmp_string_v,
        idc_nom=0.0,  # lo puedes calcular después en dominio corrientes
        voc_frio_array_v=strings_res.recomendacion.voc_string_v,
        n_strings_total=strings_res.recomendacion.n_strings_total,
        n_paneles_total=dim.n_paneles,
        strings_por_mppt=0,  # opcional: mover a strings_res después
        n_mppt=inversor.n_mppt,
        p_panel_w=panel.pmax_w,
    )

    # ======================================================
    # RECOMENDACION
    # ======================================================

    recomendacion = RecomendacionStrings(
        n_series=strings_res.recomendacion.n_series,
        n_strings_total=strings_res.recomendacion.n_strings_total,
        strings_por_mppt=0,
        vmp_string_v=strings_res.recomendacion.vmp_string_v,
        vmp_stc_string_v=strings_res.recomendacion.vmp_string_v,
        voc_frio_string_v=strings_res.recomendacion.voc_string_v,
    )

    # ======================================================
    # STRINGS → DOMAIN OBJECT
    # ======================================================

    strings_obj = [
        StringFV(
            mppt=s.mppt,
            n_series=s.n_series,
            n_strings=1,  # cada instancia es un string individual
            vmp_string_v=s.vmp_string_v,
            voc_frio_string_v=s.voc_frio_string_v,
            imp_string_a=s.imp_string_a,
            isc_string_a=s.isc_string_a,
            i_mppt_a=s.imp_string_a,
            isc_mppt_a=s.isc_string_a,
            imax_pv_a=0.0,
            idesign_cont_a=0.0,
        )
        for s in strings_res.strings
    ]

    # ======================================================
    # META
    # ======================================================

    meta = {
        "n_paneles_total": dim.n_paneles,
        "pdc_kw": dim.pdc_kw,
        "n_inversores": n_inversores,
    }

    # ======================================================
    # SALIDA FINAL
    # ======================================================

    return ResultadoPaneles(
        ok=True,
        topologia="string-centralizado",
        array=array,
        recomendacion=recomendacion,
        strings=strings_obj,
        warnings=warnings,
        errores=[],
        meta=meta,
    )
