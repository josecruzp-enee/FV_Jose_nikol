from __future__ import annotations

"""
Motor de cálculo de configuración de strings FV.

FRONTERA DEL MÓDULO
-------------------
Este módulo implementa el cálculo eléctrico de configuración
de strings del generador fotovoltaico.

Solo debe ser utilizado por:

    electrical.paneles.orquestador_paneles
"""

from math import ceil, floor
from typing import Dict, List

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


# ==========================================================
# MODELOS DE TEMPERATURA
# ==========================================================

def _voc_frio(
    voc_stc: float,
    coef_voc_pct_c: float,
    t_min_c: float,
    t_stc_c: float = 25.0
) -> float:

    return voc_stc * (1 + (coef_voc_pct_c / 100.0) * (t_min_c - t_stc_c))


def _vmp_temp(
    vmp_stc: float,
    coef_vmp_pct_c: float,
    t_oper_c: float,
    t_stc_c: float = 25.0
) -> float:

    return vmp_stc * (1 + (coef_vmp_pct_c / 100.0) * (t_oper_c - t_stc_c))


# ==========================================================
# LIMITES DE VOLTAJE
# ==========================================================

def _bounds_por_voltaje(
    panel: PanelSpec,
    inv: InversorSpec,
    t_min_c: float,
    t_oper_c: float
):

    voc_frio_panel = _voc_frio(panel.voc_v, panel.coef_voc_pct_c, t_min_c)

    vmp_hot_panel = _vmp_temp(panel.vmp_v, panel.coef_vmp_pct_c, t_oper_c)

    max_por_vdc = floor(inv.vdc_max_v / voc_frio_panel)

    min_por_mppt = ceil(inv.mppt_min_v / vmp_hot_panel)

    max_por_mppt = floor(inv.mppt_max_v / vmp_hot_panel)

    n_min = max(1, min_por_mppt)

    n_max = min(max_por_vdc, max_por_mppt)

    return n_min, n_max, voc_frio_panel, vmp_hot_panel


# ==========================================================
# SELECCION DE SERIES
# ==========================================================

# ==========================================================
# SELECCION DE SERIES (MEJORADA)
# ==========================================================

def _seleccionar_n_series(
    n_min: int,
    n_max: int,
    vmp_hot_panel: float,
    inversor: InversorSpec,
    n_paneles_total: int
):

    mid = (inversor.mppt_min_v + inversor.mppt_max_v) / 2

    best_ns = None
    best_score = float("inf")

    for n in range(n_min, n_max + 1):

        vmp_string = n * vmp_hot_panel
        error_v = abs(vmp_string - mid)

        strings = n_paneles_total // n
        paneles_usados = strings * n
        sobrantes = n_paneles_total - paneles_usados

        # ponderación
        score = error_v + (sobrantes * 50)

        if score < best_score:

            best_score = score
            best_ns = n

    return best_ns


# ==========================================================
# DISTRIBUCION ROUND ROBIN (INVERSOR / MPPT)
# ==========================================================

def distribuir_strings_por_inversor(
    n_strings_total,
    n_inversores,
    mppt_por_inversor
):

    posiciones = []

    for mppt in range(1, mppt_por_inversor + 1):
        for inv in range(1, n_inversores + 1):
            posiciones.append((inv, mppt))

    return posiciones[:n_strings_total]


# ==========================================================
# ERROR
# ==========================================================

def _resultado_error(msg: str) -> Dict:

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
    n_inversores: int,
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

    if n_inversores <= 0:
        return _resultado_error("n_inversores inválido")

    t_oper = t_oper_c if t_oper_c is not None else 55.0

    # ----------------------------------------------------------
    # LIMITES ELECTRICOS
    # ----------------------------------------------------------

    n_min, n_max, voc_frio_panel, vmp_hot_panel = _bounds_por_voltaje(
        panel,
        inversor,
        t_min_c,
        t_oper
    )

    if n_max < n_min:
        return _resultado_error("No existe número válido de módulos en serie")

    # ----------------------------------------------------------
    # SERIES
    # ----------------------------------------------------------

    n_series = _seleccionar_n_series(
        n_min,
        n_max,
        vmp_hot_panel,
        inversor,
        n_paneles_total
    )

    if not n_series:
        return _resultado_error("Serie inválida calculada")

    # ----------------------------------------------------------
    # STRINGS
    # ----------------------------------------------------------

    n_strings_total = n_paneles_total // n_series

    if n_strings_total <= 0:
        return _resultado_error("No es posible formar strings")

    resto = n_paneles_total % n_series

    if resto > 0:

        warnings.append(
            f"{resto} panel(es) no utilizados por configuración de strings"
        )

    # ----------------------------------------------------------
    # DISTRIBUCION DE STRINGS
    # ----------------------------------------------------------

    distribucion = distribuir_strings_por_inversor(
        n_strings_total,
        n_inversores,
        inversor.n_mppt
    )

    # ----------------------------------------------------------
    # GENERAR STRINGS
    # ----------------------------------------------------------

    strings = []

    vmp_string = float(n_series * vmp_hot_panel)
    voc_frio_string = float(n_series * voc_frio_panel)

    imp_string = float(panel.imp_a)
    isc_string = float(panel.isc_a)

    for i, (inv, mppt) in enumerate(distribucion, start=1):

        strings.append(
            {
                "id": i,
                "inversor": inv,
                "mppt": mppt,
                "n_series": n_series,
                "vmp_string_v": vmp_string,
                "voc_frio_string_v": voc_frio_string,
                "imp_string_a": imp_string,
                "isc_string_a": isc_string,
            }
        )

    # ----------------------------------------------------------
    # RESULTADO
    # ----------------------------------------------------------

    return {

        "ok": True,

        "errores": errores,

        "warnings": warnings,

        "strings": strings,

        "recomendacion": {

            "n_series": n_series,
            "n_strings_total": n_strings_total,

            "vmp_string_v": vmp_string,
            "voc_string_v": voc_frio_string,
        },

        "bounds": {

            "n_min": n_min,
            "n_max": n_max
        },

        "meta": {

            "n_paneles_total": n_paneles_total
        }
    }
