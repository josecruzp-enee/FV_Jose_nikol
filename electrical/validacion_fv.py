# ==========================================================
# VALIDADOR FV (SIMPLE Y CENTRALIZADO)
# ==========================================================

def validar_sistema_fv(panel, inversor, array, strings):

    errores = []
    warnings = []

    # ======================================================
    # 1. VOC FRÍO (LÍMITE DURO)
    # ======================================================
    if array.vdc_nom > inversor.vmax_dc_v:
        errores.append(
            f"Voc ({array.vdc_nom:.2f} V) excede Vdc_max del inversor ({inversor.vmax_dc_v} V)"
        )

    # ======================================================
    # 2. RANGO MPPT
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
    # 4. CORRIENTE MPPT (BÁSICO)
    # ======================================================
    try:
        if strings:
            s0 = strings[0]

            imp_string = s0.get("imp_string_a", 0)
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
