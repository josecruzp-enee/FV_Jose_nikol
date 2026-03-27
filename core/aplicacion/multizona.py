from typing import List

from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.resultado_paneles import ResultadoPaneles


def ejecutar_multizona(entradas: List) -> ResultadoPaneles:

    resultados = []

    for e in entradas:
        res = ejecutar_paneles(e)

        if not res.ok:
            return res

        resultados.append(res)

    # ==================================================
    # CONSOLIDACIÓN BÁSICA
    # ==================================================
    total_paneles = sum(r.array.n_paneles_total for r in resultados)
    total_strings = sum(r.array.n_strings_total for r in resultados)
    total_pdc = sum(r.array.potencia_dc_w for r in resultados)

    panel = resultados[0].panel

    # ==================================================
    # VALIDACIÓN VOLTAJE
    # ==================================================
    vdc_vals = [r.array.vdc_nom for r in resultados]

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

    # ==================================================
    # STRINGS CONSOLIDADOS (CLAVE)
    # ==================================================
    strings_total = []
    for r in resultados:
        strings_total.extend(r.strings)

    # ==================================================
    # MPPT TOTAL
    # ==================================================
    n_mppt_total = sum(r.array.n_mppt for r in resultados)
    strings_por_mppt = max(1, total_strings // max(1, n_mppt_total))

    # ==================================================
    # ⚠️ NO SUMAR CORRIENTES AQUÍ
    # Electrical lo hará correctamente
    # ==================================================
    idc_nom = max(r.array.idc_nom for r in resultados)
    isc_total = max(r.array.isc_total for r in resultados)

    # ==================================================
    # ARRAY FINAL
    # ==================================================
    from electrical.paneles.resultado_paneles import ArrayFV, PanelesMeta, RecomendacionStrings

    ref = resultados[0].array

    array_total = ArrayFV(
        potencia_dc_w=total_pdc,
        vdc_nom=vdc_nom,
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
    # RECOMENDACIÓN (USAR BASE, NO INVENTAR)
    # ==================================================
    recomendacion = RecomendacionStrings(
        n_series=resultados[0].recomendacion.n_series,
        n_strings_total=total_strings,
        strings_por_mppt=strings_por_mppt,
        vmp_string_v=vdc_nom,
        voc_frio_string_v=ref.voc_frio_array_v,
    )

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
        warnings=[],
        errores=[],
        meta=PanelesMeta(
            n_paneles_total=total_paneles,
            pdc_kw=total_pdc / 1000,
            n_inversores=1,
        ),
    )
