from __future__ import annotations
from typing import List
from collections import Counter

from electrical.paneles.calculo_de_strings import calcular_strings_fv
from electrical.paneles.dimensionado_paneles import dimensionar_paneles
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
)


# =========================================================
# ERROR
# =========================================================
def _resultado_error(panel, errores, warnings):
    return ResultadoPaneles(
        ok=False,
        panel=panel,
        topologia="error",
        array=None,
        recomendacion=None,
        strings=[],
        warnings=warnings or [],
        errores=errores or [],
        meta=PanelesMeta(0, 0, 0),
    )


# =========================================================
# HELPERS
# =========================================================
def _resolver_dimensionado(entrada, panel):
    if entrada.n_paneles_total is not None:
        n_paneles = entrada.n_paneles_total
        pdc_kw = (n_paneles * panel.pmax_w) / 1000
        return n_paneles, pdc_kw, None

    dim = dimensionar_paneles(entrada)

    if not dim.ok:
        return None, None, dim.errores

    return dim.n_paneles, dim.pdc_kw, None


def _strings_por_mppt_real(strings_res):
    conteo = Counter((s.inversor, s.mppt) for s in strings_res.strings)
    return max(conteo.values()) if conteo else 0


def _armar_array(
    panel,
    inversor,
    strings_res,
    n_paneles,
    pdc_kw,
    strings_por_mppt,
    n_inversores,
):
    n_strings = strings_res.recomendacion.n_strings_total

    return ArrayFV(
        potencia_dc_w=pdc_kw * 1000,
        vdc_nom=strings_res.recomendacion.vmp_string_v,
        idc_nom=None,
        isc_total=None,
        voc_frio_array_v=strings_res.recomendacion.voc_string_v,
        n_strings_total=n_strings,
        n_paneles_total=n_paneles,
        strings_por_mppt=strings_por_mppt,
        n_mppt=inversor.n_mppt * n_inversores,
        p_panel_w=panel.pmax_w,
    )


def _mapear_strings(strings_res):
    return [
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


# =========================================================
# ORQUESTADOR (SIN MULTIZONA)
# =========================================================
def ejecutar_paneles(entrada: EntradaPaneles) -> ResultadoPaneles:

    errores: List[str] = []
    warnings: List[str] = []

    panel = entrada.panel
    inversor = entrada.inversor

    # ------------------------------------------------------
    # VALIDACIÓN
    # ------------------------------------------------------
    for val in (
        validar_panel(panel),
        validar_inversor(inversor),
    ):
        errores += val.errores
        warnings += val.warnings

    if errores:
        return _resultado_error(panel, errores, warnings)

    # ======================================================
    # NORMAL (ÚNICA RESPONSABILIDAD)
    # ======================================================
    n_paneles, pdc_kw, err = _resolver_dimensionado(entrada, panel)

    if err:
        return _resultado_error(panel, err, warnings)

    strings_res = calcular_strings_fv(
        n_paneles_total=n_paneles,
        panel=panel,
        inversor=inversor,
        n_inversores=entrada.n_inversores,
        t_min_c=entrada.t_min_c,
        t_oper_c=entrada.t_oper_c,
        modo=entrada.modo,
    )

    if not strings_res.ok:
        return _resultado_error(panel, strings_res.errores, warnings)

    array = _armar_array(
        panel,
        inversor,
        strings_res,
        n_paneles,
        pdc_kw,
        _strings_por_mppt_real(strings_res),
        entrada.n_inversores,
    )

    strings = _mapear_strings(strings_res)

    meta = PanelesMeta(
        n_paneles_total=n_paneles,
        pdc_kw=pdc_kw,
        n_inversores=entrada.n_inversores,
    )

    recomendacion = RecomendacionStrings(
        n_series=strings[0].n_series,
        n_strings_total=len(strings),
        strings_por_mppt=1,
        vmp_string_v=max(s.vmp_string_v for s in strings),
        voc_frio_string_v=max(s.voc_frio_string_v for s in strings),
    )

    return ResultadoPaneles(
        ok=True,
        panel=panel,
        topologia="normal",
        array=array,
        recomendacion=recomendacion,
        strings=strings,
        warnings=warnings,
        errores=[],
        meta=meta,
    )
