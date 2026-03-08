from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PanelSpec:
    pmax_w: float
    vmp_v: float
    voc_v: float
    imp_a: float
    isc_a: float
    coef_voc_pct_c: float
    coef_vmp_pct_c: float = -0.34


@dataclass(frozen=True)
class InversorSpec:
    pac_kw: float
    vdc_max_v: float
    mppt_min_v: float
    mppt_max_v: float
    n_mppt: int
    imppt_max_a: float


def _voc_frio(voc_stc: float, coef_voc_pct_c: float, t_min_c: float, t_stc_c: float = 25.0) -> float:
    return voc_stc * (1 + (coef_voc_pct_c / 100) * (t_min_c - t_stc_c))


def _vmp_temp(vmp_stc: float, coef_vmp_pct_c: float, t_oper_c: float, t_stc_c: float = 25.0) -> float:
    return vmp_stc * (1 + (coef_vmp_pct_c / 100) * (t_oper_c - t_stc_c))


def _bounds_por_voltaje(panel: PanelSpec, inv: InversorSpec, t_min_c: float, t_oper_c: float):

    voc_frio_panel = _voc_frio(panel.voc_v, panel.coef_voc_pct_c, t_min_c)
    vmp_hot_panel = _vmp_temp(panel.vmp_v, panel.coef_vmp_pct_c, t_oper_c)

    max_por_vdc = floor(inv.vdc_max_v / voc_frio_panel)
    min_por_mppt = ceil(inv.mppt_min_v / vmp_hot_panel)
    max_por_mppt = floor(inv.mppt_max_v / panel.vmp_v)

    n_min = max(1, min_por_mppt)
    n_max = min(max_por_vdc, max_por_mppt)

    return n_min, n_max, voc_frio_panel, vmp_hot_panel


def _split_por_mppt(n_strings_total: int, n_mppt: int):

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
) -> Dict[str, Any]:

    errores: List[str] = []
    warnings: List[str] = []

    if n_paneles_total <= 0:
        return {
            "ok": False,
            "errores": ["n_paneles_total inválido"],
            "warnings": [],
            "strings": [],
            "recomendacion": {},
            "bounds": {},
            "meta": {},
        }

    t_oper = t_oper_c if t_oper_c else 55.0

    n_min, n_max, voc_frio_panel, vmp_hot_panel = _bounds_por_voltaje(
        panel, inversor, t_min_c, t_oper
    )

    if n_max < n_min:
        return {
            "ok": False,
            "errores": ["No existe número válido de módulos en serie"],
            "warnings": [],
            "strings": [],
            "recomendacion": {},
            "bounds": {},
            "meta": {},
        }

    # ==========================================================
    # Elegir número de módulos en serie
    # ==========================================================

    mid = (inversor.mppt_min_v + inversor.mppt_max_v) / 2

    best_ns = None
    best_error = 1e12

    for n in range(n_min, n_max + 1):

        vmp_string = n * vmp_hot_panel
        err = abs(vmp_string - mid)

        if err < best_error:
            best_error = err
            best_ns = n

    n_series = best_ns

    # ==========================================================
    # Número de strings
    # ==========================================================

    n_strings_total = n_paneles_total // n_series

    if n_strings_total <= 0:

        return {
            "ok": False,
            "errores": [
                f"No es posible formar strings con {n_paneles_total} paneles y {n_series} por string"
            ],
            "warnings": [],
            "strings": [],
            "recomendacion": {},
            "bounds": {},
            "meta": {},
        }

    paneles_usados = n_strings_total * n_series
    paneles_sobrantes = n_paneles_total - paneles_usados

    if paneles_sobrantes > 0:

        warnings.append(
            f"{paneles_sobrantes} panel(es) no utilizados por configuración de strings"
        )

    ramas = _split_por_mppt(n_strings_total, inversor.n_mppt)

    strings = []

    for r in ramas:

        n_paralelo = r["n_strings"]

        isc_array = panel.isc_a * n_paralelo
        imax_pv = 1.25 * isc_array
        idesign = 1.56 * isc_array

        if imax_pv > inversor.imppt_max_a:

            errores.append(
                f"MPPT {r['mppt']} excede corriente máxima"
            )

        strings.append(
            {
                "mppt": r["mppt"],
                "n_series": n_series,
                "n_paralelo": n_paralelo,
                "vmp_string_v": n_series * vmp_hot_panel,
                "voc_frio_string_v": n_series * voc_frio_panel,
                "imp_a": panel.imp_a,
                "isc_a": panel.isc_a,
                "i_mppt_a": panel.imp_a * n_paralelo,
                "isc_array_a": isc_array,
                "imax_pv_a": imax_pv,
                "idesign_cont_a": idesign,
            }
        )

    # ==========================================================
    # Potencias
    # ==========================================================

    p_string_kw = (panel.pmax_w * n_series) / 1000
    pdc_total_kw = p_string_kw * n_strings_total

    recomendacion = {
        "n_series": n_series,
        "n_strings_total": n_strings_total,
        "p_string_kw_stc": p_string_kw,
        "pdc_total_kw_stc": pdc_total_kw,
        "vmp_string_v": n_series * vmp_hot_panel,
        "voc_frio_string_v": n_series * voc_frio_panel,
    }

    meta = {
        "n_paneles_total": n_paneles_total,
        "paneles_usados": paneles_usados,
        "paneles_sobrantes": paneles_sobrantes,
    }

    # ==========================================================
    # 👇 DATOS PARA MOTOR DE CORRIENTES
    # ==========================================================

    strings_por_mppt = 0
    imp_string = 0
    isc_string = 0

    if strings:

        imp_string = strings[0]["imp_a"]
        isc_string = strings[0]["isc_a"]

        strings_por_mppt = strings[0]["n_paralelo"]

    corrientes_input = {

        "imp_string_a": imp_string,
        "isc_string_a": isc_string,
        "strings_por_mppt": strings_por_mppt,
        "n_strings_total": n_strings_total

    }

    # ==========================================================

    return {
        "ok": len(errores) == 0,
        "errores": errores,
        "warnings": warnings,
        "strings": strings,
        "recomendacion": recomendacion,
        "bounds": {
            "n_min": n_min,
            "n_max": n_max,
        },
        "meta": meta,
        "corrientes_input": corrientes_input,
    }
        "meta": meta,
    }
