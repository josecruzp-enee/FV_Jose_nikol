from __future__ import annotations
from typing import List

from electrical.paneles.calculo_de_strings import calcular_strings_fv
from electrical.paneles.dimensionado_paneles import dimensionar_paneles
from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.paneles.resultado_paneles import (
    ResultadoPaneles,
    ArrayFV,
    StringFV,
    RecomendacionStrings,
    PanelesMeta,
)
from electrical.paneles.validacion_strings import (
    validar_panel,
    validar_inversor,
    validar_parametros_generales,
)


def _resultado_error(errores: List[str], warnings: List[str]) -> ResultadoPaneles:

    return ResultadoPaneles(
        ok=False,
        topologia="error",
        array=ArrayFV(0,0,0,0,0,0,0,0,0,0),
        recomendacion=RecomendacionStrings(0,0,0,0,0),
        strings=[],
        warnings=warnings,
        errores=errores,
        meta=PanelesMeta(0,0,0),
    )


def ejecutar_paneles(entrada: EntradaPaneles) -> ResultadoPaneles:

    errores: List[str] = []
    warnings: List[str] = []

    panel = entrada.panel
    inversor = entrada.inversor

    # ------------------------------------------------------
    # VALIDACIÓN
    # ------------------------------------------------------

    val = validar_panel(panel)
    errores += val.errores
    warnings += val.warnings

    val = validar_inversor(inversor)
    errores += val.errores
    warnings += val.warnings

    if entrada.n_paneles_total is not None:
        val = validar_parametros_generales(
            entrada.n_paneles_total,
            entrada.t_min_c,
            entrada.t_oper_c,
        )
        errores += val.errores
        warnings += val.warnings

    if errores:
        return _resultado_error(errores, warnings)

    # ------------------------------------------------------
    # DIMENSIONADO (MANUAL vs AUTOMÁTICO)
    # ------------------------------------------------------

    if entrada.n_paneles_total is not None:
        # 🔹 MODO MANUAL
        n_paneles = entrada.n_paneles_total
        pdc_kw = (n_paneles * panel.pmax_w) / 1000

    else:
        # 🔹 MODO AUTOMÁTICO
        dim = dimensionar_paneles(entrada)

        if not dim.ok:
            return _resultado_error(dim.errores, warnings)

        n_paneles = dim.n_paneles
        pdc_kw = dim.pdc_kw

    # ------------------------------------------------------
    # STRINGS
    # ------------------------------------------------------

    n_inversores = int(entrada.n_inversores or 1)

    strings_res = calcular_strings_fv(
        n_paneles_total=n_paneles,
        panel=panel,
        inversor=inversor,
        n_inversores=n_inversores,
        t_min_c=entrada.t_min_c,
        t_oper_c=entrada.t_oper_c,
    )

    if not strings_res.ok:
        return _resultado_error(strings_res.errores, warnings)

    n_strings = strings_res.recomendacion.n_strings_total

    # ------------------------------------------------------
    # ARRAY
    # ------------------------------------------------------

    idc_nom = panel.imp_a * n_strings
    isc_total = panel.isc_a * n_strings

    strings_por_mppt = max(1, n_strings // inversor.n_mppt)

    array = ArrayFV(
        potencia_dc_w=pdc_kw * 1000,
        vdc_nom=strings_res.recomendacion.vmp_string_v,
        idc_nom=idc_nom,
        isc_total=isc_total,
        voc_frio_array_v=strings_res.recomendacion.voc_string_v,
        n_strings_total=n_strings,
        n_paneles_total=n_paneles,
        strings_por_mppt=strings_por_mppt,
        n_mppt=inversor.n_mppt,
        p_panel_w=panel.pmax_w,
    )

    # ------------------------------------------------------
    # STRINGS
    # ------------------------------------------------------

    strings = [
        StringFV(
            mppt=s.mppt,
            n_series=s.n_series,
            vmp_string_v=s.vmp_string_v,
            voc_frio_string_v=s.voc_frio_string_v,
            imp_string_a=s.imp_string_a,
            isc_string_a=s.isc_string_a,
        )
        for s in strings_res.strings
    ]

    # ------------------------------------------------------
    # META
    # ------------------------------------------------------

    meta = PanelesMeta(
        n_paneles_total=n_paneles,
        pdc_kw=pdc_kw,
        n_inversores=n_inversores,
    )

    # ------------------------------------------------------
    # RESULTADO FINAL
    # ------------------------------------------------------

    return ResultadoPaneles(
        ok=True,
        topologia="string-centralizado",
        array=array,
        recomendacion=RecomendacionStrings(
            n_series=strings_res.recomendacion.n_series,
            n_strings_total=n_strings,
            strings_por_mppt=strings_por_mppt,
            vmp_string_v=strings_res.recomendacion.vmp_string_v,
            voc_frio_string_v=strings_res.recomendacion.voc_string_v,
        ),
        strings=strings,
        warnings=warnings,
        errores=[],
        meta=meta,
    )
