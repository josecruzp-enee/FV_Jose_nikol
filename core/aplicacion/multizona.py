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

    # 🔥 CONSOLIDACIÓN
    total_paneles = sum(r.array.n_paneles_total for r in resultados)
    total_strings = sum(r.array.n_strings_total for r in resultados)
    total_idc = sum(r.array.idc_nom for r in resultados)
    total_isc = sum(r.array.isc_total for r in resultados)
    total_pdc = sum(r.array.potencia_dc_w for r in resultados)

    # tomar referencia
    ref = resultados[0].array
    panel = resultados[0].panel

    # strings totales
    strings_total = []
    for r in resultados:
        strings_total.extend(r.strings)

    from electrical.paneles.resultado_paneles import ArrayFV, PanelesMeta, RecomendacionStrings

    array_total = ArrayFV(
        potencia_dc_w=total_pdc,
        vdc_nom=ref.vdc_nom,
        idc_nom=total_idc,
        isc_total=total_isc,
        voc_frio_array_v=ref.voc_frio_array_v,
        n_strings_total=total_strings,
        n_paneles_total=total_paneles,
        strings_por_mppt=ref.strings_por_mppt,
        n_mppt=ref.n_mppt,
        p_panel_w=ref.p_panel_w,
    )

    return ResultadoPaneles(
        ok=True,
        panel=panel,
        topologia="multizona",
        array=array_total,
        recomendacion=RecomendacionStrings(
            n_series=ref.vdc_nom,  # puedes mejorar luego
            n_strings_total=total_strings,
            strings_por_mppt=ref.strings_por_mppt,
            vmp_string_v=ref.vdc_nom,
            voc_frio_string_v=ref.voc_frio_array_v,
        ),
        strings=strings_total,
        warnings=[],
        errores=[],
        meta=PanelesMeta(
            n_paneles_total=total_paneles,
            pdc_kw=total_pdc / 1000,
            n_inversores=1,
        ),
    )
