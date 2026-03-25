# ==========================================================
# HELPERS
# ==========================================================

def _calcular_voc_frio(voc, t_min_c, coef=0.003):
    return voc * (1 + coef * (25 - t_min_c))


def _limites_string(panel, inversor, t_min_c):

    voc_frio = _calcular_voc_frio(panel.voc_v, t_min_c)

    # 🔥 VALIDACIÓN DOMINIO
    if not hasattr(inversor, "vdc_max_v"):
        raise ValueError("Inversor sin atributo vdc_max_v")

    vmax = inversor.vdc_max_v

    max_series = int(vmax / voc_frio)
    min_series = max(1, int(inversor.mppt_min_v / panel.vmp_v))

    return min_series, max_series


def _evaluar_config(n_paneles_total, n_series):

    n_strings = n_paneles_total / n_series

    if n_strings < 1:
        return None

    n_strings = int(round(n_strings))
    total_calc = n_strings * n_series
    error = abs(total_calc - n_paneles_total)

    return n_strings, error


def _buscar_mejor_config(n_paneles_total, min_series, max_series):

    mejor = None

    for n_series in range(min_series, max_series + 1):

        res = _evaluar_config(n_paneles_total, n_series)

        if res is None:
            continue

        n_strings, error = res

        if mejor is None or error < mejor["error"]:
            mejor = {
                "n_series": n_series,
                "n_strings_total": n_strings,
                "error": error,
            }

    return mejor


def _validar_config(config, panel, inversor):

    warnings = []

    n_series = config["n_series"]
    n_strings = config["n_strings_total"]

    # 🔹 MPPT vs strings
    if n_strings > inversor.n_mppt:
        warnings.append("Más strings que MPPT disponibles")

    # 🔹 Vmp rango MPPT
    vmp_string = n_series * panel.vmp_v

    if not (inversor.mppt_min_v <= vmp_string <= inversor.mppt_max_v):
        warnings.append("Vmp fuera de rango MPPT")

    # 🔹 Voc frío límite
    voc_frio = _calcular_voc_frio(panel.voc_v, 10)
    voc_string = n_series * voc_frio

    if voc_string > inversor.vdc_max_v:
        warnings.append("Voc frío excede límite del inversor")

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
    min_series, max_series = _limites_string(panel, inversor, t_min_c)

    if max_series < 1:
        return {"ok": False, "error": "Voc excede límite inversor"}

    # =============================
    # BUSQUEDA
    # =============================
    mejor = _buscar_mejor_config(n_paneles_total, min_series, max_series)

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
        mejor["n_strings_total"],
        inversor.n_mppt
    )

    # =============================
    # MODELO ELÉCTRICO
    # =============================
    strings_list = _construir_strings(panel, mejor["n_strings_total"])

    # =============================
    # RESULTADO FINAL
    # =============================
    return {
        "ok": True,
        "n_series": mejor["n_series"],
        "n_strings_total": mejor["n_strings_total"],
        "strings_por_mppt": strings_por_mppt,
        "strings": strings_list,
        "warnings": warnings,
    }
