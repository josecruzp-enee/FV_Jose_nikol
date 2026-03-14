from __future__ import annotations

"""
MOTOR DE CÁLCULO DE CONFIGURACIÓN DE STRINGS FV
================================================

Este módulo calcula la configuración eléctrica del generador
fotovoltaico en términos de:

    - número de módulos en serie
    - número total de strings
    - distribución de strings por inversor / MPPT
    - voltajes del string
    - corrientes del string

Este módulo SOLO implementa lógica eléctrica del generador FV.

NO calcula:
    - energía
    - HSP
    - PR
    - pérdidas del sistema
    - consumo energético

----------------------------------------------------------
ENTRADAS
----------------------------------------------------------

panel : PanelSpec

    voc_v
    vmp_v
    isc_a
    imp_a
    pmax_w
    coef_voc_pct_c
    coef_vmp_pct_c


inversor : InversorSpec

    vdc_max_v
    mppt_min_v
    mppt_max_v
    imppt_max_a
    n_mppt
    kw_ac


n_paneles_total : int
    número total de módulos del generador FV

n_inversores : int
    número de inversores del sistema

t_min_c : float
    temperatura mínima del sitio (usada para Voc frío)

t_oper_c : float
    temperatura típica de operación del panel

dos_aguas : bool
    indica si el generador tiene orientación doble

objetivo_dc_ac : float | None
    ratio DC/AC objetivo

pdc_kw_objetivo : float | None
    potencia DC objetivo


----------------------------------------------------------
SALIDA
----------------------------------------------------------

dict

{
    ok : bool
    errores : list[str]
    warnings : list[str]

    strings : list[dict]

    recomendacion :
        n_series
        n_strings_total
        vmp_string_v
        voc_string_v

    bounds :
        n_min
        n_max

    meta :
        n_paneles_total
}
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
    """
    Calcula el Voc corregido a temperatura mínima.

    Fórmula:

        Voc(T) = Voc_STC * (1 + coef_voc * ΔT)

    ΔT = t_min_c − 25°C
    """

    return voc_stc * (1 + (coef_voc_pct_c / 100.0) * (t_min_c - t_stc_c))


def _vmp_temp(
    vmp_stc: float,
    coef_vmp_pct_c: float,
    t_oper_c: float,
    t_stc_c: float = 25.0
) -> float:
    """
    Calcula Vmp corregido a temperatura de operación.
    """

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
    """
    Determina el rango permitido de módulos en serie.

    Condiciones verificadas:

        Voc_frio_string <= Vdc_max inversor
        Vmp_operacion_string dentro ventana MPPT
    """

    voc_frio_panel = _voc_frio(panel.voc_v, panel.coef_voc_pct_c, t_min_c)

    vmp_hot_panel = _vmp_temp(panel.vmp_v, panel.coef_vmp_pct_c, t_oper_c)

    # límite por voltaje máximo DC
    max_por_vdc = floor(inv.vdc_max_v / voc_frio_panel)

    # límite por ventana MPPT
    min_por_mppt = ceil(inv.mppt_min_v / vmp_hot_panel)

    max_por_mppt = floor(inv.mppt_max_v / vmp_hot_panel)

    n_min = max(1, min_por_mppt)

    n_max = min(max_por_vdc, max_por_mppt)

    return n_min, n_max, voc_frio_panel, vmp_hot_panel


# ==========================================================
# SELECCION DE SERIES
# ==========================================================

def _seleccionar_n_series(
    n_min: int,
    n_max: int,
    vmp_hot_panel: float,
    inversor: InversorSpec,
    n_paneles_total: int
):
    """
    Selecciona el número óptimo de módulos en serie.

    Estrategia:

        - acercar Vmp_string al centro de ventana MPPT
        - minimizar paneles sobrantes
    """

    mid = (inversor.mppt_min_v + inversor.mppt_max_v) / 2

    best_ns = None
    best_score = float("inf")

    for n in range(n_min, n_max + 1):

        vmp_string = n * vmp_hot_panel
        error_v = abs(vmp_string - mid)

        strings = n_paneles_total // n
        paneles_usados = strings * n
        sobrantes = n_paneles_total - paneles_usados

        # heurística de optimización
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
    """
    Distribuye los strings entre inversores y MPPT
    usando algoritmo round-robin.
    """

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

    # temperatura típica de operación
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
    # SELECCION DE SERIES
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
    # VERIFICACION CORRIENTE MPPT
    # ----------------------------------------------------------

    if inversor.imppt_max_a > 0:

        strings_por_mppt = ceil(
            n_strings_total / (n_inversores * inversor.n_mppt)
        )

        corriente_mppt = strings_por_mppt * panel.isc_a

        if corriente_mppt > inversor.imppt_max_a:

            warnings.append(
                "Posible exceso de corriente en MPPT "
                f"({corriente_mppt:.2f} A > {inversor.imppt_max_a:.2f} A)"
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

    # en un string las corrientes NO se suman
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
