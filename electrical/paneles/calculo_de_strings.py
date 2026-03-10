from __future__ import annotations

from math import ceil, floor
from typing import Dict, List

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


# ==========================================================
# TEMPERATURA
# ==========================================================

def _voc_frio(voc_stc: float, coef_voc_frac_c: float, t_min_c: float, t_stc_c: float = 25.0):
    return voc_stc * (1 + coef_voc_frac_c * (t_min_c - t_stc_c))


# ==========================================================
# LIMITES DE VOLTAJE
# ==========================================================

def _bounds_por_voltaje(panel: PanelSpec, inv: InversorSpec, t_min_c: float, t_oper_c: float):

    voc_frio_panel = _voc_frio(
        panel.voc_v,
        panel.coef_voc_pct_c / 100.0,
        t_min_c
    )

    vmp_hot_panel = panel.vmp_v

    max_por_vdc = floor(inv.vdc_max_v / voc_frio_panel)

    min_por_mppt = ceil(inv.mppt_min_v / vmp_hot_panel)

    max_por_mppt = floor(inv.mppt_max_v / vmp_hot_panel)

    n_min = max(1, min_por_mppt)

    n_max = min(max_por_vdc, max_por_mppt)

    return n_min, n_max, voc_frio_panel, vmp_hot_panel


# ==========================================================
# SELECCION SERIES
# ==========================================================

def _seleccionar_n_series(n_min: int, n_max: int, vmp_hot_panel: float, inversor: InversorSpec):

    mid = (inversor.mppt_min_v + inversor.mppt_max_v) / 2

    best_ns = None
    best_error = 1e12

    for n in range(n_min, n_max + 1):

        vmp_string = n * vmp_hot_panel
        err = abs(vmp_string - mid)

        if err < best_error:
            best_error = err
            best_ns = n

    return best_ns


# ==========================================================
# DISTRIBUCION STRINGS
# ==========================================================

def _split_por_mppt(n_strings_total: int, inversor: InversorSpec):

    n_mppt = inversor.n_mppt

    base = n_strings_total // n_mppt
    resto = n_strings_total % n_mppt

    salida = []

    for i in range(n_mppt):

        n = base + (1 if i < resto else 0)

        if n > 0:
            salida.append(
                {
                    "mppt": i + 1,
                    "n_strings": n
                }
            )

    return salida


# ==========================================================
# GENERACION STRINGS
# ==========================================================

def _generar_strings(ramas, n_series, panel: PanelSpec, voc_frio_panel, vmp_hot_panel):

    strings = []

    for r in ramas:

        n_paralelo = r["n_strings"]

        strings.append(
            {
                "mppt": r["mppt"],
                "n_series": n_series,
                "n_paralelo": n_paralelo,

                "vmp_string_v": n_series * vmp_hot_panel,
                "voc_frio_string_v": n_series * voc_frio_panel,

                "imp_string_a": panel.imp_a,
                "isc_string_a": panel.isc_a,

                "imp_mppt_a": panel.imp_a * n_paralelo,
                "isc_array_a": panel.isc_a * n_paralelo,
            }
        )

    return strings


# ==========================================================
# RESULTADO ERROR
# ==========================================================

def _resultado_error(msg: str):

    return {
        "ok": False,
        "errores": [msg],
        "warnings": [],
        "strings": [],
        "recomendacion": {},
        "bounds": {},
        "meta": {}
    }


# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def calcular_strings_fv(
    *,
    n_paneles_total: int,
    panel: PanelSpec,
    inversor: InversorSpec,
    t_min_c: float,
    dos_aguas: bool = False,
    objetivo_dc_ac: float | None = None,
    pdc_kw_objetivo: float | None = None,
    t_oper_c: float | None = None,
) -> Dict:

    errores: List[str] = []
    warnings: List[str] = []

    if n_paneles_total <= 0:
        return _resultado_error("n_paneles_total inválido")

    t_oper = t_oper_c if t_oper_c else 55.0

    n_min, n_max, voc_frio_panel, vmp_hot_panel = _bounds_por_voltaje(
        panel,
        inversor,
        t_min_c,
        t_oper
    )

    if n_max < n_min:
        return _resultado_error("No existe número válido de módulos en serie")

    n_series = _seleccionar_n_series(
        n_min,
        n_max,
        vmp_hot_panel,
        inversor
    )

    if not n_series or n_series <= 0:
        return _resultado_error("Serie inválida calculada")

    n_strings_total = n_paneles_total // n_series

    if n_strings_total <= 0:
        return _resultado_error("No es posible formar strings")

    ramas = _split_por_mppt(
        n_strings_total,
        inversor
    )

    strings = _generar_strings(
        ramas,
        n_series,
        panel,
        voc_frio_panel,
        vmp_hot_panel
    )

    vmp_string = vmp_hot_panel * n_series
    voc_string = voc_frio_panel * n_series

    for s in strings:

        s["imp_a"] = float(panel.imp_a)
        s["isc_a"] = float(panel.isc_a)

        s["vmp_string_v"] = float(vmp_string)
        s["voc_string_v"] = float(voc_string)

    return {
        "ok": True,
        "errores": errores,
        "warnings": warnings,
        "strings": strings,
        "recomendacion": {
            "n_series": n_series,
            "n_strings_total": n_strings_total,
            "vmp_string_v": vmp_string,
            "voc_string_v": voc_string
        },
        "bounds": {
            "n_min": n_min,
            "n_max": n_max
        },
        "meta": {
            "n_paneles_total": n_paneles_total
        }
    }
