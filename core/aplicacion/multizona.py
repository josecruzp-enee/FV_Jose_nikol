from typing import List

from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.resultado_paneles import ResultadoPaneles


def ejecutar_multizona(entradas: List) -> ResultadoPaneles:

    resultados = []

    # ==================================================
    # EJECUCIÓN POR ZONA
    # ==================================================
    for e in entradas:
        res = ejecutar_paneles(e)

        if not res.ok:
            return res

        resultados.append(res)

    if not resultados:
        return ResultadoPaneles(
            ok=False,
            panel=None,
            topologia="multizona",
            array=None,
            recomendacion=None,
            strings=[],
            warnings=[],
            errores=["No hay resultados válidos en zonas"],
            meta=None,
        )

    panel = resultados[0].panel

    # ==================================================
    # 🔥 DETALLE POR ZONA (CLAVE)
    # ==================================================
    zonas_detalle = []

    for i, r in enumerate(resultados, 1):

        zonas_detalle.append({
            "zona": i,
            "paneles": r.meta.n_paneles_total if r.meta else None,
            "pdc_kw": r.meta.pdc_kw if r.meta else None,
            "strings": len(r.strings) if r.strings else 0,
            "vdc": r.array.vdc_nom if r.array else None,
            "idc": r.array.idc_nom if r.array else None,
            "isc": r.array.isc_total if r.array else None,
        })

    # ==================================================
    # CONSOLIDACIÓN SEGURA
    # ==================================================
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

    # ==================================================
    # VALIDACIÓN DE VOLTAJE
    # ==================================================
    vdc_vals = [
        (r.array.vdc_nom if r.array else None)
        for r in resultados
        if (r.array and r.array.vdc_nom is not None)
    ]

    if vdc_vals:
        if max(vdc_vals) - min(vdc_vals) > 20:
            return ResultadoPaneles(
                ok=False,
                panel=panel,
                topologia="multizona",
                array=None,
                recomendacion=None,
                strings=[],
                warnings=[],
                errores=["Voltajes incompatibles entre zonas"],
                meta=None,
            )

        vdc_nom = sum(vdc_vals) / len(vdc_vals)
    else:
        vdc_nom = None

    # ==================================================
    # STRINGS CONSOLIDADOS
    # ==================================================
    strings_total = []
    for r in resultados:
        if r.strings:
            strings_total.extend(r.strings)

    # ==================================================
    # MPPT TOTAL
    # ==================================================
    n_mppt_total = sum(
        (r.array.n_mppt if r.array else 0)
        for r in resultados
    )

    strings_por_mppt = (
        max(1, total_strings // max(1, n_mppt_total))
        if n_mppt_total > 0 else 1
    )

    # ==================================================
    # ⚠️ CORRIENTES (PARALELO)
    # ==================================================
    idc_nom = max(
        (r.array.idc_nom for r in resultados if r.array),
        default=0
    )

    isc_total = max(
        (r.array.isc_total for r in resultados if r.array),
        default=0
    )

    # ==================================================
    # ARRAY FINAL
    # ==================================================
    from electrical.paneles.resultado_paneles import (
        ArrayFV,
        PanelesMeta,
        RecomendacionStrings,
    )

    ref = next((r.array for r in resultados if r.array), None)

    if ref is None:
        return ResultadoPaneles(
            ok=False,
            panel=panel,
            topologia="multizona",
            array=None,
            recomendacion=None,
            strings=strings_total,
            warnings=["No se pudo construir array consolidado"],
            errores=[],
            meta=None,
        )

    array_total = ArrayFV(
        potencia_dc_w=total_pdc,
        vdc_nom=vdc_nom or ref.vdc_nom,
        idc_nom=idc_nom,
        isc_total=isc_total,
        voc_frio_array_v=ref.voc_frio_array_v,
        n_strings_total=total_strings,
        n_paneles_total=total_paneles,
        strings_por_mppt=strings_por_mppt,
        n_mppt=n_mppt_total,
        p_panel_w=ref.p_panel_w,
    )

    # ==================================================
    # RECOMENDACIÓN
    # ==================================================
    rec_base = resultados[0].recomendacion

    recomendacion = RecomendacionStrings(
        n_series=rec_base.n_series if rec_base else None,
        n_strings_total=total_strings,
        strings_por_mppt=strings_por_mppt,
        vmp_string_v=vdc_nom or ref.vdc_nom,
        voc_frio_string_v=ref.voc_frio_array_v,
    )

    # ==================================================
    # WARNINGS CONSOLIDADOS
    # ==================================================
    warnings = []
    for r in resultados:
        warnings.extend(r.warnings or [])

    # ==================================================
    # RESULTADO FINAL
    # ==================================================
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
            "zonas": zonas_detalle,   # 🔥 AQUÍ ESTÁ LO IMPORTANTE
        },
    )
