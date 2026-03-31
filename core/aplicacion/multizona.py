from typing import List

from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.resultado_paneles import ResultadoPaneles


# ==========================================================
# MAIN
# ==========================================================
def ejecutar_multizona(entradas: List) -> ResultadoPaneles:

    resultados = _ejecutar_zonas(entradas)

    if isinstance(resultados, ResultadoPaneles):
        return resultados  # error temprano

    if not resultados:
        return _error("No hay resultados válidos en zonas")

    panel = resultados[0].panel

    zonas_detalle = _build_zonas_detalle(resultados)

    total_paneles, total_strings, total_pdc = _calcular_totales(resultados)

    vdc_nom = _validar_voltajes(resultados, panel)

    strings_total = _consolidar_strings(resultados)

    n_mppt_total, strings_por_mppt = _calcular_mppt(resultados, total_strings)

    array_total = _build_array(
        resultados,
        total_paneles,
        total_strings,
        total_pdc,
        vdc_nom,
        n_mppt_total,
        strings_por_mppt,
    )

    recomendacion = _build_recomendacion(resultados, total_strings, strings_por_mppt, vdc_nom)

    warnings = _collect_warnings(resultados)

    return ResultadoPaneles(
        ok=True,
        panel=panel,
        topologia="multizona",
        array=array_total,
        recomendacion=recomendacion,
        strings=strings_total,
        warnings=warnings,
        errores=[],
        meta={
            "n_paneles_total": total_paneles,
            "pdc_kw": total_pdc / 1000,
            "n_inversores": 1,
            "zonas": zonas_detalle,
        },
    )


# ==========================================================
# ZONAS
# ==========================================================
def _ejecutar_zonas(entradas):

    resultados = []

    for e in entradas:
        res = ejecutar_paneles(e)

        if not res.ok:
            return res

        resultados.append(res)

    return resultados


# ==========================================================
# DETALLE
# ==========================================================
def _build_zonas_detalle(resultados):

    zonas = []

    for i, r in enumerate(resultados, 1):
        zonas.append({
            "zona": i,
            "paneles": r.meta.n_paneles_total if r.meta else None,
            "pdc_kw": r.meta.pdc_kw if r.meta else None,
            "strings": len(r.strings) if r.strings else 0,
            "vdc": r.array.vdc_nom if r.array else None,
            "idc": r.array.idc_nom if r.array else None,
            "isc": r.array.isc_total if r.array else None,
        })

    return zonas


# ==========================================================
# TOTALES
# ==========================================================
def _calcular_totales(resultados):

    total_paneles = sum(
        (r.array.n_paneles_total if r.array else r.meta.n_paneles_total)
        for r in resultados
    )

    total_strings = sum(
        (r.array.n_strings_total if r.array else 0)
        for r in resultados
    )

    total_pdc = sum(
        (r.array.potencia_dc_w if r.array else r.meta.pdc_kw * 1000)
        for r in resultados
    )

    return total_paneles, total_strings, total_pdc


# ==========================================================
# VOLTAJE
# ==========================================================
def _validar_voltajes(resultados, panel):

    vdc_vals = [
        r.array.vdc_nom
        for r in resultados
        if (r.array and r.array.vdc_nom is not None)
    ]

    if not vdc_vals:
        return None

    if max(vdc_vals) - min(vdc_vals) > 20:
        raise ValueError("Voltajes incompatibles entre zonas")

    return vdc_vals[0]


# ==========================================================
# STRINGS
# ==========================================================
def _consolidar_strings(resultados):

    strings = []

    for i, r in enumerate(resultados):
        if r.strings:
            for s in r.strings:
                s.zona = i + 1
                strings.append(s)

    return strings


# ==========================================================
# MPPT
# ==========================================================
def _calcular_mppt(resultados, total_strings):

    n_mppt_total = sum(
        (r.array.n_mppt if r.array else 0)
        for r in resultados
    )

    strings_por_mppt = (
        max(1, total_strings // max(1, n_mppt_total))
        if n_mppt_total > 0 else 1
    )

    return n_mppt_total, strings_por_mppt


# ==========================================================
# ARRAY
# ==========================================================
def _build_array(
    resultados,
    total_paneles,
    total_strings,
    total_pdc,
    vdc_nom,
    n_mppt_total,
    strings_por_mppt,
):

    from electrical.paneles.resultado_paneles import ArrayFV

    ref = next((r.array for r in resultados if r.array), None)

    if ref is None:
        return None

    return ArrayFV(
        potencia_dc_w=total_pdc,
        vdc_nom=vdc_nom or ref.vdc_nom,
        idc_nom=None,
        isc_total=None,
        voc_frio_array_v=ref.voc_frio_array_v,
        n_strings_total=total_strings,
        n_paneles_total=total_paneles,
        strings_por_mppt=strings_por_mppt,
        n_mppt=n_mppt_total,
        p_panel_w=ref.p_panel_w,
    )


# ==========================================================
# RECOMENDACIÓN
# ==========================================================
def _build_recomendacion(resultados, total_strings, strings_por_mppt, vdc_nom):

    from electrical.paneles.resultado_paneles import RecomendacionStrings

    rec_base = resultados[0].recomendacion
    ref = resultados[0].array

    return RecomendacionStrings(
        n_series=rec_base.n_series if rec_base else None,
        n_strings_total=total_strings,
        strings_por_mppt=strings_por_mppt,
        vmp_string_v=vdc_nom or ref.vdc_nom,
        voc_frio_string_v=ref.voc_frio_array_v,
    )


# ==========================================================
# WARNINGS
# ==========================================================
def _collect_warnings(resultados):

    warnings = []

    for r in resultados:
        warnings.extend(r.warnings or [])

    return warnings


# ==========================================================
# ERROR
# ==========================================================
def _error(msg):

    return ResultadoPaneles(
        ok=False,
        panel=None,
        topologia="multizona",
        array=None,
        recomendacion=None,
        strings=[],
        warnings=[],
        errores=[msg],
        meta=None,
    )
