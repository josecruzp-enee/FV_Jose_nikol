from __future__ import annotations

"""
MOTOR DE CÁLCULO DE STRINGS FV — VERSION TIPADA
==============================================

Este módulo calcula la configuración eléctrica del generador FV:

    - número de módulos en serie
    - número de strings
    - distribución por MPPT
    - voltajes
    - corrientes

REGLA:
    NO usa dict
    SOLO usa dataclass
"""

from dataclasses import dataclass
from math import ceil, floor
from typing import List, Optional

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


# =========================================================
# RESULTADOS TIPADOS
# =========================================================

@dataclass(frozen=True)
class StringCalc:
    inversor: int
    mppt: int

    n_series: int

    vmp_string_v: float
    voc_frio_string_v: float

    imp_string_a: float
    isc_string_a: float


@dataclass(frozen=True)
class RecomendacionCalc:
    n_series: int
    n_strings_total: int

    vmp_string_v: float
    voc_string_v: float


@dataclass(frozen=True)
class BoundsCalc:
    n_min: int
    n_max: int


@dataclass(frozen=True)
class StringsResultado:
    ok: bool

    errores: List[str]
    warnings: List[str]

    strings: List[StringCalc]

    recomendacion: RecomendacionCalc
    bounds: BoundsCalc

    n_paneles_total: int


# =========================================================
# MODELOS DE TEMPERATURA
# =========================================================

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


# =========================================================
# LIMITES
# =========================================================

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


# =========================================================
# SELECCION
# =========================================================

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

        score = error_v + (sobrantes * 50)

        if score < best_score:
            best_score = score
            best_ns = n

    return best_ns


# =========================================================
# DISTRIBUCION
# =========================================================

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


# =========================================================
# MOTOR PRINCIPAL
# =========================================================

def calcular_strings_fv(
    *,
    n_paneles_total: int,
    panel: PanelSpec,
    inversor: InversorSpec,
    n_inversores: int,
    t_min_c: float,
    dos_aguas: bool = False,
    objetivo_dc_ac: Optional[float] = None,
    pdc_kw_objetivo: Optional[float] = None,
    t_oper_c: Optional[float] = None,
) -> StringsResultado:

    errores: List[str] = []
    warnings: List[str] = []

    if n_paneles_total <= 0:
        return StringsResultado(
            ok=False,
            errores=["n_paneles_total inválido"],
            warnings=[],
            strings=[],
            recomendacion=RecomendacionCalc(0, 0, 0.0, 0.0),
            bounds=BoundsCalc(0, 0),
            n_paneles_total=0
        )

    if n_inversores <= 0:
        return StringsResultado(
            ok=False,
            errores=["n_inversores inválido"],
            warnings=[],
            strings=[],
            recomendacion=RecomendacionCalc(0, 0, 0.0, 0.0),
            bounds=BoundsCalc(0, 0),
            n_paneles_total=0
        )

    t_oper = t_oper_c if t_oper_c is not None else 55.0

    # LIMITES
    n_min, n_max, voc_frio_panel, vmp_hot_panel = _bounds_por_voltaje(
        panel,
        inversor,
        t_min_c,
        t_oper
    )

    if n_max < n_min:
        return StringsResultado(
            ok=False,
            errores=["No existe número válido de módulos en serie"],
            warnings=[],
            strings=[],
            recomendacion=RecomendacionCalc(0, 0, 0.0, 0.0),
            bounds=BoundsCalc(0, 0),
            n_paneles_total=0
        )

    # SELECCION
    n_series = _seleccionar_n_series(
        n_min,
        n_max,
        vmp_hot_panel,
        inversor,
        n_paneles_total
    )

    if not n_series:
        return StringsResultado(
            ok=False,
            errores=["Serie inválida calculada"],
            warnings=[],
            strings=[],
            recomendacion=RecomendacionCalc(0, 0, 0.0, 0.0),
            bounds=BoundsCalc(0, 0),
            n_paneles_total=0
        )

    # STRINGS
    n_strings_total = n_paneles_total // n_series

    if n_strings_total <= 0:
        return StringsResultado(
            ok=False,
            errores=["No es posible formar strings"],
            warnings=[],
            strings=[],
            recomendacion=RecomendacionCalc(0, 0, 0.0, 0.0),
            bounds=BoundsCalc(0, 0),
            n_paneles_total=0
        )

    resto = n_paneles_total % n_series

    if resto > 0:
        warnings.append(f"{resto} panel(es) no utilizados")

    # DISTRIBUCION
    distribucion = distribuir_strings_por_inversor(
        n_strings_total,
        n_inversores,
        inversor.n_mppt
    )

    # CALCULOS
    vmp_string = float(n_series * vmp_hot_panel)
    voc_frio_string = float(n_series * voc_frio_panel)

    imp_string = float(panel.imp_a)
    isc_string = float(panel.isc_a)

    strings = [
        StringCalc(
            inversor=inv,
            mppt=mppt,
            n_series=n_series,
            vmp_string_v=vmp_string,
            voc_frio_string_v=voc_frio_string,
            imp_string_a=imp_string,
            isc_string_a=isc_string,
        )
        for (inv, mppt) in distribucion
    ]

    return StringsResultado(
        ok=True,
        errores=errores,
        warnings=warnings,
        strings=strings,
        recomendacion=RecomendacionCalc(
            n_series=n_series,
            n_strings_total=n_strings_total,
            vmp_string_v=vmp_string,
            voc_string_v=voc_frio_string
        ),
        bounds=BoundsCalc(
            n_min=n_min,
            n_max=n_max
        ),
        n_paneles_total=n_paneles_total
    )
