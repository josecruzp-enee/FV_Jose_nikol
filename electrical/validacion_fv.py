# ==========================================================
# VALIDADOR FV (CORREGIDO - NIVEL INGENIERÍA)
# ==========================================================

def validar_sistema_fv(panel, inversor, array, strings):

    errores = []
    warnings = []

    # ======================================================
    # 1. VOC FRÍO (CORRECTO POR STRING)
    # ======================================================
    try:
        if strings:
            for i, s in enumerate(strings):
                voc_string = getattr(s, "voc_frio_string_v", None)

                if voc_string and getattr(inversor, "vmax_dc_v", None):
                    if voc_string > inversor.vmax_dc_v:
                        errores.append(
                            f"String {i+1}: Voc frío ({voc_string:.2f} V) excede Vdc_max ({inversor.vmax_dc_v} V)"
                        )
    except Exception:
        warnings.append("No se pudo validar Voc frío")

    # ======================================================
    # 2. RANGO MPPT (Vmp)
    # ======================================================
    try:
        if not (inversor.mppt_min_v <= array.vdc_nom <= inversor.mppt_max_v):
            warnings.append(
                f"Vmp ({array.vdc_nom:.2f} V) fuera de rango MPPT "
                f"({inversor.mppt_min_v} - {inversor.mppt_max_v} V)"
            )
    except Exception:
        warnings.append("No se pudo validar rango MPPT")

    # ======================================================
    # 3. STRINGS POR MPPT
    # ======================================================
    try:
        if getattr(array, "strings_por_mppt", 0) > 2:
            warnings.append(
                f"Demasiados strings por MPPT ({array.strings_por_mppt})"
            )
    except Exception:
        warnings.append("No se pudo validar strings por MPPT")

    # ======================================================
    # 4. CORRIENTE MPPT (CORRECTO)
    # ======================================================
    try:
        if strings:
            imppt_max = getattr(inversor, "imppt_max_a", None)

            for i, s in enumerate(strings):
                imp_string = getattr(s, "imp_string_a", 0)
                i_mppt = imp_string * getattr(array, "strings_por_mppt", 1)

                if imppt_max and i_mppt > imppt_max:
                    errores.append(
                        f"String {i+1}: Corriente MPPT ({i_mppt:.2f} A) excede límite ({imppt_max} A)"
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
