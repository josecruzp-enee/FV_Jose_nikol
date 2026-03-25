# ==========================================================
# HELPERS
# ==========================================================

def _calcular_voc_frio(voc, t_min_c, coef=0.003):
    return voc * (1 + coef * (25 - t_min_c))


def _limites_string(panel, inversor, t_min_c):

    voc_frio = _calcular_voc_frio(panel.voc_v, t_min_c)

    max_ps = int(inversor.vmax_dc_v / voc_frio)
    min_ps = max(1, int(inversor.mppt_min_v / panel.vmp_v))

    return min_ps, max_ps


def _evaluar_config(n_paneles_total, nps):

    n_strings = n_paneles_total / nps

    if n_strings < 1:
        return None

    n_strings = int(round(n_strings))
    total_calc = n_strings * nps
    error = abs(total_calc - n_paneles_total)

    return n_strings, error


def _buscar_mejor_config(n_paneles_total, min_ps, max_ps):

    mejor = None

    for nps in range(min_ps, max_ps + 1):

        res = _evaluar_config(n_paneles_total, nps)

        if res is None:
            continue

        n_strings, error = res

        if mejor is None or error < mejor["error"]:
            mejor = {
                "paneles_por_string": nps,
                "n_strings": n_strings,
                "error": error,
            }

    return mejor


def _validar_config(config, panel, inversor):

    warnings = []

    nps = config["paneles_por_string"]
    n_strings = config["n_strings"]

    # MPPT
    if n_strings > inversor.n_mppt:
        warnings.append("Más strings que MPPT disponibles")

    # Rango MPPT
    vmp_string = nps * panel.vmp_v

    if not (inversor.mppt_min_v <= vmp_string <= inversor.mppt_max_v):
        warnings.append("Vmp fuera de rango MPPT")

    return warnings


def _calcular_strings_por_mppt(n_strings, n_mppt):
    n_mppt = max(1, n_mppt)
    return max(1, int(round(n_strings / n_mppt)))


def _construir_strings(panel, n_strings):

    return [
        {
            "imp_string_a": panel.imp_a,
            "isc_string_a": panel.isc_a,
        }
        for _ in range(n_strings)
    ]


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def calcular_strings_fv(
    n_paneles_total,
    panel,
    inversor,
    t_min_c=10
):

    # =============================
    # LIMITES
    # =============================
    min_ps, max_ps = _limites_string(panel, inversor, t_min_c)

    if max_ps < 1:
        return {"ok": False, "error": "Voc excede límite inversor"}

    # =============================
    # BUSQUEDA
    # =============================
    mejor = _buscar_mejor_config(n_paneles_total, min_ps, max_ps)

    if mejor is None:
        return {"ok": False, "error": "No se pudo dimensionar strings"}

    # =============================
    # VALIDACIÓN
    # =============================
    warnings = _validar_config(mejor, panel, inversor)

    # =============================
    # DISTRIBUCIÓN MPPT
    # =============================
    strings_por_mppt = _calcular_strings_por_mppt(
        mejor["n_strings"],
        inversor.n_mppt
    )

    # =============================
    # MODELO ELÉCTRICO
    # =============================
    strings_list = _construir_strings(panel, mejor["n_strings"])

    # =============================
    # RESULTADO FINAL
    # =============================
    return {
        "ok": True,
        "paneles_por_string": mejor["paneles_por_string"],
        "n_strings": mejor["n_strings"],
        "strings_por_mppt": strings_por_mppt,
        "strings": strings_list,
        "warnings": warnings,
    }
