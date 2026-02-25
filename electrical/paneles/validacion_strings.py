# Validación del dominio paneles: verifica coherencia de datos de entrada sin ejecutar cálculos FV.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple


# Modelo simple de panel usado solo para validar datos provenientes de UI/API.
@dataclass(frozen=True)
class PanelFV:
    voc_stc: float
    vmp_stc: float
    isc: float
    imp: float
    coef_voc_pct_c: float
    pmax_w: float = 0.0


# Modelo simple de inversor usado solo para validar datos provenientes de UI/API.
@dataclass(frozen=True)
class InversorFV:
    vdc_max: float
    mppt_min: float
    mppt_max: float
    imppt_max: float
    n_mppt: int
    pac_kw: float = 0.0


# Convierte cualquier valor a float seguro.
def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


# Convierte cualquier valor a entero seguro.
def _i(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return int(default)


# Valida coherencia básica de parámetros del panel FV.
def validar_panel(panel: PanelFV) -> Tuple[List[str], List[str]]:
    errores: List[str] = []
    warnings: List[str] = []

    if panel.voc_stc <= 0 or panel.vmp_stc <= 0:
        errores.append("Panel inválido: Voc/Vmp deben ser > 0.")

    if panel.isc <= 0 or panel.imp <= 0:
        errores.append("Panel inválido: Isc/Imp deben ser > 0.")

    if panel.coef_voc_pct_c >= 0:
        warnings.append("coef_voc_pct_c normalmente es negativo.")

    return errores, warnings


# Valida coherencia básica de parámetros del inversor.
def validar_inversor(inversor: InversorFV) -> Tuple[List[str], List[str]]:
    errores: List[str] = []
    warnings: List[str] = []

    if inversor.vdc_max <= 0:
        errores.append("Inversor inválido: vdc_max <= 0.")

    if inversor.mppt_min <= 0 or inversor.mppt_max <= 0:
        errores.append("Inversor inválido: ventana MPPT inválida.")

    if inversor.mppt_min >= inversor.mppt_max:
        errores.append("mppt_min debe ser menor que mppt_max.")

    if inversor.imppt_max <= 0:
        errores.append("imppt_max debe ser > 0 (dato obligatorio datasheet).")

    if inversor.n_mppt <= 0:
        errores.append("n_mppt inválido.")

    return errores, warnings


# Valida parámetros generales del cálculo de strings.
def validar_parametros_generales(
    n_paneles_total: int,
    temp_min: float,
) -> Tuple[List[str], List[str]]:
    errores: List[str] = []
    warnings: List[str] = []

    if _i(n_paneles_total, 0) <= 0:
        errores.append("n_paneles_total inválido (<=0).")

    try:
        float(temp_min)
    except Exception:
        errores.append("temp_min no convertible a número.")

    return errores, warnings
