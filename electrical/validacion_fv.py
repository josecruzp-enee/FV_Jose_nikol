# ==========================================================
# VALIDADOR FV (CORREGIDO - NIVEL INGENIERÍA)
# ==========================================================

def validar_sistema_fv(panel, inversor, array, strings):

    errores = []
    warnings = []

    # ======================================================
    # 1. VOC FRÍO (CRÍTICO - NEC)
    # ======================================================
    try:
        voc_panel = getattr(panel, "voc_v", None)
        n_paneles = int(array.vdc_nom / panel.vmp_v) if panel.vmp_v else 0

        if voc_panel and n_paneles:
            # Factor típico frío (puedes hacerlo dinámico luego)
            factor_frio = 1.25
            voc_frio = voc_panel * n_paneles * factor_frio

            if voc_frio > inversor.vmax_dc_v:
                errores.append(
                    f"Voc frío ({voc_frio:.2f} V) excede Vdc_max ({inversor.vmax_dc_v} V)"
                )

    except Exception:
        warnings.append("No se pudo validar Voc frío")

    # ======================================================
    # 2. RANGO MPPT (Vmp)
    # ======================================================
    if not (inversor.mppt_min_v <= array.vdc_nom <= inversor.mppt_max_v):
        warnings.append(
            f"Vmp ({array.vdc_nom:.2f} V) fuera de rango MPPT "
            f"({inversor.mppt_min_v} - {inversor.mppt_max_v} V)"
        )

    # ======================================================
    # 3. STRINGS POR MPPT
    # ======================================================
    if array.strings_por_mppt > 2:
        warnings.append(
            f"Demasiados strings por MPPT ({array.strings_por_mppt})"
        )

    # ======================================================
    # 4. CORRIENTE MPPT
    # ======================================================
    try:
        if strings:
            s0 = strings[0]

            imp_string = getattr(s0, "imp_string_a", 0)
            i_mppt = imp_string * array.strings_por_mppt

            if hasattr(inversor, "imax_mppt_a") and inversor.imax_mppt_a:
                if i_mppt > inversor.imax_mppt_a:
                    errores.append(
                        f"Corriente MPPT ({i_mppt:.2f} A) excede límite ({inversor.imax_mppt_a} A)"
                    )
    except Exception:
        warnings.append("No se pudo validar corriente MPPT")

    # ======================================================
    # RESULTADO FINAL
    # ======================================================
    return {
        "ok": len(errores) == 0,
        "errores": errores,
        "warnings": warnings,
    }
