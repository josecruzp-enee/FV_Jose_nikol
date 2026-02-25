# Validación del dominio paneles: verifica coherencia de PanelSpec/InversorSpec y parámetros previos al motor FV.
from __future__ import annotations

from typing import List, Optional, Tuple

from .calculo_de_strings import InversorSpec, PanelSpec


# Valida coherencia básica de parámetros del panel FV usando el contrato interno PanelSpec.
def validar_panel(panel: PanelSpec) -> Tuple[List[str], List[str]]:
    errores: List[str] = []
    warnings: List[str] = []

    if panel.voc_v <= 0 or panel.vmp_v <= 0:
        errores.append("Panel inválido: Voc/Vmp deben ser > 0.")

    if panel.isc_a <= 0 or panel.imp_a <= 0:
        errores.append("Panel inválido: Isc/Imp deben ser > 0.")

    if panel.pmax_w <= 0:
        warnings.append("Panel: pmax_w <= 0 (revisar catálogo).")

    if panel.coef_voc_pct_c >= 0:
        warnings.append("Panel: coef_voc_pct_c normalmente es negativo.")

    if panel.coef_vmp_pct_c >= 0:
        warnings.append("Panel: coef_vmp_pct_c normalmente es negativo.")

    # Coherencia suave: Vmp no debería exceder Voc (no es norma, pero suele ser error de carga)
    if panel.voc_v > 0 and panel.vmp_v > panel.voc_v:
        warnings.append("Panel: Vmp > Voc (posible error de datos).")

    return errores, warnings


# Valida coherencia básica de parámetros del inversor usando el contrato interno InversorSpec.
def validar_inversor(inversor: InversorSpec) -> Tuple[List[str], List[str]]:
    errores: List[str] = []
    warnings: List[str] = []

    if inversor.vdc_max_v <= 0:
        errores.append("Inversor inválido: vdc_max_v <= 0.")

    if inversor.mppt_min_v <= 0 or inversor.mppt_max_v <= 0:
        errores.append("Inversor inválido: ventana MPPT inválida (<=0).")

    if inversor.mppt_min_v >= inversor.mppt_max_v:
        errores.append("Inversor inválido: mppt_min_v debe ser < mppt_max_v.")

    # A norma: dato obligatorio datasheet
    if inversor.imppt_max_a <= 0:
        errores.append("Inversor inválido: imppt_max_a debe ser > 0 (dato obligatorio datasheet).")

    if inversor.n_mppt <= 0:
        errores.append("Inversor inválido: n_mppt <= 0.")

    # Check suave: no necesariamente error, pero requiere revisión
    if inversor.vdc_max_v > 0 and inversor.mppt_max_v > 0 and inversor.vdc_max_v < inversor.mppt_max_v:
        warnings.append("Inversor: vdc_max_v < mppt_max_v (revisar datasheet).")

    if inversor.pac_kw <= 0:
        warnings.append("Inversor: pac_kw <= 0 (DC/AC objetivo puede quedar sin referencia).")

    return errores, warnings


# Valida parámetros generales previos al cálculo de strings (no ejecuta cálculos eléctricos).
def validar_parametros_generales(
    n_paneles_total: int,
    t_min_c: float,
    t_oper_c: Optional[float] = None,
) -> Tuple[List[str], List[str]]:
    errores: List[str] = []
    warnings: List[str] = []

    if int(n_paneles_total) <= 0:
        errores.append("n_paneles_total inválido (<=0).")

    try:
        float(t_min_c)
    except Exception:
        errores.append("t_min_c no convertible a número.")

    if t_oper_c is not None:
        try:
            float(t_oper_c)
        except Exception:
            errores.append("t_oper_c no convertible a número.")

    return errores, warnings
