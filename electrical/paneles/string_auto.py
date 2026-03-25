def calcular_strings_fv(
    n_paneles_total,
    panel,
    inversor,
    t_min_c=10
):

    voc = panel.voc_v
    vmp = panel.vmp_v
    isc = panel.isc_a

    vdc_max = inversor.vmax_dc_v
    mppt_min = inversor.mppt_min_v
    mppt_max = inversor.mppt_max_v
    n_mppt = inversor.n_mppt

    # =============================
    # CORRECCIÓN VOC FRÍO
    # =============================
    coef_temp = 0.003
    voc_frio = voc * (1 + coef_temp * (25 - t_min_c))

    max_paneles_string = int(vdc_max / voc_frio)
    min_paneles_string = max(1, int(mppt_min / vmp))

    if max_paneles_string < 1:
        return {"ok": False, "error": "Voc excede límite inversor"}

    # =============================
    # ITERAR SOLUCIÓN
    # =============================
    mejor = None

    for nps in range(min_paneles_string, max_paneles_string + 1):

        n_strings = n_paneles_total / nps

        if n_strings < 1:
            continue

        n_strings = int(round(n_strings))

        total_calc = n_strings * nps

        error = abs(total_calc - n_paneles_total)

        if mejor is None or error < mejor["error"]:

            mejor = {
                "paneles_por_string": nps,
                "n_strings": n_strings,
                "error": error,
            }

    if mejor is None:
        return {"ok": False, "error": "No se pudo dimensionar strings"}

    # =============================
    # VALIDACIONES
    # =============================
    warnings = []

    if mejor["n_strings"] > n_mppt:
        warnings.append("Más strings que MPPT disponibles")

    vmp_string = mejor["paneles_por_string"] * vmp

    if not (mppt_min <= vmp_string <= mppt_max):
        warnings.append("Vmp fuera de rango MPPT")

    return {
        "ok": True,
        "paneles_por_string": mejor["paneles_por_string"],
        "n_strings": mejor["n_strings"],
        "warnings": warnings,
    }
