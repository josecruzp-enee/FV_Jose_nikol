from dataclasses import dataclass
from math import ceil, floor
from typing import List, Optional
from collections import Counter

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


# =========================================================
# RESULTADOS
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
# TEMPERATURA
# =========================================================

def _voc_frio(voc, coef, t_min):
    return voc * (1 + coef / 100 * (t_min - 25))


def _vmp_temp(vmp, coef, t_oper):
    return vmp * (1 + coef / 100 * (t_oper - 25))


# =========================================================
# LIMITES
# =========================================================

def _bounds(panel, inv, t_min, t_oper):
    voc = _voc_frio(panel.voc_v, panel.coef_voc_pct_c, t_min)
    vmp = _vmp_temp(panel.vmp_v, panel.coef_vmp_pct_c, t_oper)

    n_min = ceil(inv.mppt_min_v / vmp)
    n_max = floor(inv.vdc_max_v / voc)

    return max(1, n_min), max(1, n_max), voc, vmp


def _strings_por_mppt_max(panel, inv) -> int:
    imp = float(getattr(panel, "imp_a", 0.0) or 0.0)
    imppt_max = float(getattr(inv, "imppt_max_a", 0.0) or 0.0)

    if imp <= 0 or imppt_max <= 0:
        return 1

    return max(1, floor(imppt_max / imp))


# =========================================================
# DISTRIBUCIÓN
# =========================================================

def _distribuir(n_strings, n_inv, n_mppt, strings_por_mppt_max):
    posiciones = []

    capacidad_total = n_inv * n_mppt * strings_por_mppt_max

    if n_strings > capacidad_total:
        raise ValueError(
            f"No hay capacidad suficiente para distribuir strings: "
            f"{n_strings} strings > {n_inv} inversores × {n_mppt} MPPT "
            f"× {strings_por_mppt_max} strings/MPPT = {capacidad_total} strings."
        )

    for inv in range(1, n_inv + 1):
        for mppt in range(1, n_mppt + 1):
            for _ in range(strings_por_mppt_max):
                if len(posiciones) >= n_strings:
                    return posiciones

                posiciones.append((inv, mppt))

    return posiciones


def _max_strings_por_mppt_usado(posiciones) -> int:
    if not posiciones:
        return 0

    conteo = Counter(posiciones)
    return max(conteo.values())


# =========================================================
# SELECCIÓN GENERALIZADA
# =========================================================

def _seleccionar(
    n_min,
    n_max,
    vmp,
    inv,
    n_total,
    strings_por_mppt_max,
    n_inversores,
):
    target = (inv.mppt_min_v + inv.mppt_max_v) / 2

    best = None
    best_score = None

    for n_series in range(n_min, n_max + 1):

        n_strings = ceil(n_total / n_series)

        if n_strings <= 0:
            continue

        paneles_usados = n_strings * n_series
        sobrantes_virtuales = paneles_usados - n_total

        capacidad = n_inversores * inv.n_mppt * strings_por_mppt_max

        if n_strings > capacidad:
            continue

        v_string = n_series * vmp
        error_v = abs(v_string - target)

        score = (
            sobrantes_virtuales,
            n_strings,
            error_v,
            abs(n_series - ((n_min + n_max) / 2)),
        )

        if best_score is None or score < best_score:
            best_score = score
            best = n_series

    return best


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def calcular_strings_fv(
    *,
    n_paneles_total: int,
    panel: PanelSpec,
    inversor: InversorSpec,
    n_inversores: int,
    t_min_c: float,
    t_oper_c: Optional[float] = 55.0,
    modo: str = "auto",
) -> StringsResultado:

    warnings: List[str] = []

    if n_paneles_total <= 0:
        return StringsResultado(
            False,
            ["Paneles inválidos"],
            [],
            [],
            RecomendacionCalc(0, 0, 0, 0),
            BoundsCalc(0, 0),
            0,
        )

    if n_inversores <= 0:
        return StringsResultado(
            False,
            ["Cantidad de inversores inválida"],
            [],
            [],
            RecomendacionCalc(0, 0, 0, 0),
            BoundsCalc(0, 0),
            n_paneles_total,
        )

    n_min, n_max, voc_panel, vmp_panel = _bounds(
        panel,
        inversor,
        t_min_c,
        t_oper_c,
    )

    if n_max < n_min:
        return StringsResultado(
            False,
            ["No hay rango válido"],
            [],
            [],
            RecomendacionCalc(0, 0, 0, 0),
            BoundsCalc(n_min, n_max),
            n_paneles_total,
        )

    strings_por_mppt_max = _strings_por_mppt_max(panel, inversor)

    # ======================================================
    # SELECCIÓN
    # ======================================================
    if modo in ("manual", "multizona"):
        n_series = n_paneles_total

        if n_series < n_min:
            warnings.append(
                f"String muy corto ({n_series} paneles) → menor que mínimo MPPT ({n_min})"
            )

        if n_series > n_max:
            warnings.append(
                f"String muy largo ({n_series} paneles) → supera máximo permitido ({n_max})"
            )

    else:
        n_series = _seleccionar(
            n_min=n_min,
            n_max=n_max,
            vmp=vmp_panel,
            inv=inversor,
            n_total=n_paneles_total,
            strings_por_mppt_max=strings_por_mppt_max,
            n_inversores=n_inversores,
        )

    if not n_series:
        return StringsResultado(
            False,
            [
                "No se pudo seleccionar una configuración de strings válida "
                "para el inversor seleccionado."
            ],
            warnings,
            [],
            RecomendacionCalc(0, 0, 0, 0),
            BoundsCalc(n_min, n_max),
            n_paneles_total,
        )

    # ======================================================
    # STRINGS
    # ======================================================
    n_strings = ceil(n_paneles_total / n_series)

    paneles_configurados = n_strings * n_series

    if paneles_configurados != n_paneles_total:
        warnings.append(
            f"Distribución no exacta: {n_paneles_total} paneles reales, "
            f"{n_strings} strings × {n_series} paneles = {paneles_configurados}. "
            "Revise si desea ajustar número de paneles o strings."
        )

    # ======================================================
    # DISTRIBUCIÓN
    # ======================================================
    try:
        distrib = _distribuir(
            n_strings=n_strings,
            n_inv=n_inversores,
            n_mppt=inversor.n_mppt,
            strings_por_mppt_max=strings_por_mppt_max,
        )
    except Exception as exc:
        return StringsResultado(
            False,
            [str(exc)],
            warnings,
            [],
            RecomendacionCalc(0, 0, 0, 0),
            BoundsCalc(n_min, n_max),
            n_paneles_total,
        )

    max_paralelo_usado = _max_strings_por_mppt_usado(distrib)

    corriente_mppt = max_paralelo_usado * float(panel.imp_a)
    corriente_mppt_max = float(inversor.imppt_max_a)

    if corriente_mppt > corriente_mppt_max:
        return StringsResultado(
            False,
            [
                f"Corriente MPPT excedida: {corriente_mppt:.2f} A > "
                f"{corriente_mppt_max:.2f} A."
            ],
            warnings,
            [],
            RecomendacionCalc(0, 0, 0, 0),
            BoundsCalc(n_min, n_max),
            n_paneles_total,
        )

    if max_paralelo_usado > 1:
        warnings.append(
            f"Se usan hasta {max_paralelo_usado} strings en paralelo por MPPT. "
            f"Corriente máxima estimada por MPPT: {corriente_mppt:.2f} A."
        )

    # ======================================================
    # PARÁMETROS
    # ======================================================
    vmp_string = n_series * vmp_panel
    voc_string = n_series * voc_panel

    strings = [
        StringCalc(
            inversor=i,
            mppt=m,
            n_series=n_series,
            vmp_string_v=vmp_string,
            voc_frio_string_v=voc_string,
            imp_string_a=float(panel.imp_a),
            isc_string_a=float(panel.isc_a),
        )
        for (i, m) in distrib
    ]

    return StringsResultado(
        ok=True,
        errores=[],
        warnings=warnings,
        strings=strings,
        recomendacion=RecomendacionCalc(
            n_series=n_series,
            n_strings_total=n_strings,
            vmp_string_v=vmp_string,
            voc_string_v=voc_string,
        ),
        bounds=BoundsCalc(n_min, n_max),
        n_paneles_total=n_paneles_total,
    )
