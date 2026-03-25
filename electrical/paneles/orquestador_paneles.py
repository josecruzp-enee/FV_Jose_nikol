from __future__ import annotations
from typing import List
from collections import Counter

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
        idc_nom=panel.imp_a * n_strings,
        isc_total=panel.isc_a * n_strings,
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
# ORQUESTADOR
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

    if entrada.n_paneles_total is not None:
        val = validar_parametros_generales(
            entrada.n_paneles_total,
            entrada.t_min_c,
            entrada.t_oper_c,
        )
        errores += val.errores
        warnings += val.warnings

    if errores:
        return _resultado_error(panel, errores, warnings)

    # ------------------------------------------------------
    # DIMENSIONADO
    # ------------------------------------------------------

    n_paneles, pdc_kw, err = _resolver_dimensionado(entrada, panel)

    if err:
        return _resultado_error(panel, err, warnings)

    # ------------------------------------------------------
    # INVERSORES
    # ------------------------------------------------------

    if entrada.n_inversores is None:
        return _resultado_error(
            panel,
            ["n_inversores no definido desde core (sizing)"],
            warnings
        )

    n_inversores = int(entrada.n_inversores)

    # ------------------------------------------------------
    # STRINGS (motor)
    # ------------------------------------------------------

    strings_res = calcular_strings_fv(
        n_paneles_total=n_paneles,
        panel=panel,
        inversor=inversor,
        n_inversores=n_inversores,
        t_min_c=entrada.t_min_c,
        t_oper_c=entrada.t_oper_c,
    )

    if not strings_res.ok:
        return _resultado_error(panel, strings_res.errores, warnings)

    # ------------------------------------------------------
    # DISTRIBUCIÓN
    # ------------------------------------------------------

    strings_por_mppt = _strings_por_mppt_real(strings_res)

    if strings_por_mppt <= 0:
        strings_por_mppt = 1
        warnings.append("strings_por_mppt ajustado a 1")

    # ------------------------------------------------------
    # ENSAMBLE
    # ------------------------------------------------------

    array = _armar_array(
        panel,
        inversor,
        strings_res,
        n_paneles,
        pdc_kw,
        strings_por_mppt,
        n_inversores,
    )

    if array.n_mppt <= 0:
        return _resultado_error(panel, ["n_mppt inválido"], warnings)

    if array.n_strings_total <= 0:
        return _resultado_error(panel, ["n_strings_total inválido"], warnings)

    if array.n_strings_total < array.n_mppt:
        warnings.append(
            f"Strings insuficientes para MPPT ({array.n_strings_total}/{array.n_mppt})"
        )

    strings = _mapear_strings(strings_res)

    meta = PanelesMeta(
        n_paneles_total=n_paneles,
        pdc_kw=pdc_kw,
        n_inversores=n_inversores,
    )

    print("\nDEBUG PANEL FINAL:")
    print("n_inversores:", n_inversores)
    print("n_strings:", array.n_strings_total)
    print("n_mppt:", array.n_mppt)
    print("strings/mppt:", array.strings_por_mppt)

    topologia = "string" if n_inversores > 1 else "centralizado"

    return ResultadoPaneles(
        ok=True,
        panel=panel,
        topologia=topologia,
        array=array,
        recomendacion=RecomendacionStrings(
            n_series=strings_res.recomendacion.n_series,
            n_strings_total=strings_res.recomendacion.n_strings_total,
            strings_por_mppt=strings_por_mppt,
            vmp_string_v=strings_res.recomendacion.vmp_string_v,
            voc_frio_string_v=strings_res.recomendacion.voc_string_v,
        ),
        strings=strings,
        warnings=warnings,
        errores=[],
        meta=meta,
    )
