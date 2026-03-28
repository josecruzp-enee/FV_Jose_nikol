from dataclasses import dataclass
from math import ceil, floor
from typing import List, Optional

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


# =========================================================
# SELECCIÓN AUTOMÁTICA
# =========================================================

def _seleccionar(n_min, n_max, vmp, inv, n_total):

    target = (inv.mppt_min_v + inv.mppt_max_v) / 2

    best = None
    best_score = float("inf")

    for n in range(n_min, n_max + 1):

        n_strings = n_total // n
        if n_strings < 1:
            continue

        sobrantes = n_total - (n_strings * n)
        v_string = n * vmp

        error_v = abs(v_string - target)
        score = error_v + sobrantes * 100

        if score < best_score:
            best_score = score
            best = n

    return best


# =========================================================
# SELECCIÓN FIJA (ESTRICTA)
# =========================================================

def _seleccionar_fijo(n_min, n_max, n_total):

    candidatos = []

    for n in range(n_min, n_max + 1):
        if n_total % n == 0:
            candidatos.append(n)

    if not candidatos:
        return None  # 🔴 NO INVENTAR

    return max(candidatos)  # preferir strings largos


# =========================================================
# DISTRIBUCIÓN
# =========================================================

def _distribuir(n_strings, n_inv, n_mppt):

    posiciones = []
    carga = [(i, m, 0) for i in range(1, n_inv+1) for m in range(1, n_mppt+1)]

    for _ in range(n_strings):
        carga.sort(key=lambda x: x[2])
        i, m, c = carga[0]
        posiciones.append((i, m))
        carga[0] = (i, m, c + 1)

    return posiciones


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
    modo: str = "auto",   # 🔥 CAMBIO CLAVE
) -> StringsResultado:

    warnings: List[str] = []

    if n_paneles_total <= 0:
        return StringsResultado(False, ["Paneles inválidos"], [], [], RecomendacionCalc(0,0,0,0), BoundsCalc(0,0), 0)

    # límites eléctricos
    n_min, n_max, voc_panel, vmp_panel = _bounds(panel, inversor, t_min_c, t_oper_c)

    if n_max < n_min:
        return StringsResultado(False, ["No hay rango válido de serie"], [], [], RecomendacionCalc(0,0,0,0), BoundsCalc(0,0), 0)

    # =====================================================
    # SELECCIÓN
    # =====================================================
    if modo in ("manual", "multizona"):
        n_series = _seleccionar_fijo(n_min, n_max, n_paneles_total)
    else:
        n_series = _seleccionar(n_min, n_max, vmp_panel, inversor, n_paneles_total)

    if not n_series:
        return StringsResultado(False, ["No existe combinación válida"], [], [], RecomendacionCalc(0,0,0,0), BoundsCalc(0,0), 0)

    # =====================================================
    # STRINGS
    # =====================================================
    if modo in ("manual", "multizona"):

        if n_paneles_total % n_series != 0:
            return StringsResultado(
                False,
                [f"No existe combinación exacta para {n_paneles_total} paneles"],
                [],
                [],
                RecomendacionCalc(0,0,0,0),
                BoundsCalc(n_min, n_max),
                n_paneles_total
            )

        n_strings = n_paneles_total // n_series

    else:
        n_strings = n_paneles_total // n_series

    if n_strings < 1:
        return StringsResultado(False, ["No es posible formar strings"], [], [], RecomendacionCalc(0,0,0,0), BoundsCalc(0,0), 0)

    # VALIDACIÓN FINAL
    if modo in ("manual", "multizona"):
        if n_series * n_strings != n_paneles_total:
            return StringsResultado(
                False,
                ["Violación interna: configuración no exacta"],
                [],
                [],
                RecomendacionCalc(0,0,0,0),
                BoundsCalc(n_min, n_max),
                n_paneles_total
            )

    # =====================================================
    # DISTRIBUCIÓN
    # =====================================================
    distrib = _distribuir(n_strings, n_inversores, inversor.n_mppt)

    # parámetros eléctricos
    vmp_string = n_series * vmp_panel
    voc_string = n_series * voc_panel

    imp = panel.imp_a
    isc = panel.isc_a

    strings = [
        StringCalc(
            inversor=i,
            mppt=m,
            n_series=n_series,
            vmp_string_v=vmp_string,
            voc_frio_string_v=voc_string,
            imp_string_a=imp,
            isc_string_a=isc,
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
            voc_string_v=voc_string
        ),
        bounds=BoundsCalc(n_min, n_max),
        n_paneles_total=n_paneles_total
    )
