# Validación del dominio paneles: verifica coherencia de datos eléctricos antes de ejecutar el motor FV.
from __future__ import annotations

from typing import List, Tuple

from .calculo_de_strings import PanelSpec, InversorSpec


# Valida coherencia básica de parámetros del panel FV usando el contrato interno PanelSpec.
def validar_panel(panel: PanelSpec) -> Tuple[List[str], List[str]]:
    errores: List[str] = []
    warnings: List[str] = []

    if panel.voc_v <= 0 or panel.vmp_v <= 0:
        errores.append("Panel inválido: Voc/Vmp deben ser > 0.")

    if panel.isc_a <= 0 or panel.imp_a <= 0:
        errores.append("Panel inválido: Isc/Imp deben ser > 0.")

    if panel.pmax_w <= 0:
        warnings.append("pmax_w <= 0 (revisar catálogo del panel).")

    if panel.coef_voc_pct_c >= 0:
        warnings.append("coef_voc_pct_c normalmente es negativo.")

    if panel.coef_vmp_pct_c >= 0:
        warnings.append("coef_vmp_pct_c normalmente es negativo.")

    return errores, warnings


# Valida coherencia básica de parámetros del inversor usando el contrato interno InversorSpec.
def validar_inversor(inversor: InversorSpec) -> Tuple[List[str], List[str]]:
    errores: List[str] = []
    warnings: List[str] = []

    if inversor.vdc_max_v <= 0:
        errores.append("Inversor inválido: vdc_max_v <= 0.")

    if inversor.mppt_min_v <= 0 or inversor.mppt_max_v <= 0:
        errores.append("Inversor inválido: ventana MPPT inválida.")

    if inversor.mppt_min_v >= inversor.mppt_max_v:
        errores.append("mppt_min_v debe ser menor que mppt_max_v.")

    if inversor.imppt_max_a <= 0:
        errores.append("imppt_max_a debe ser > 0 (dato obligatorio datasheet).")

    if inversor.n_mppt <= 0:
        errores.append("n_mppt inválido.")

    if inversor.vdc_max_v < inversor.mppt_max_v:
        warnings.append("vdc_max_v < mppt_max_v (revisar datasheet).")

    return errores, warnings


# Valida parámetros generales previos al cálculo de strings.
def validar_parametros_generales(
    n_paneles_total: int,
    temp_min: float,
) -> Tuple[List[str], List[str]]:
    errores: List[str] = []
    warnings: List[str] = []

    if int(n_paneles_total) <= 0:
        errores.append("n_paneles_total inválido (<=0).")

    try:
        float(temp_min)
    except Exception:
        errores.append("temp_min no convertible a número.")

    return errores, warnings
