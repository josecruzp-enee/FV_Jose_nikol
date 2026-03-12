"""
Factores de corrección NEC — FV Engine

FRONTERA DEL MÓDULO
-------------------

Este módulo implementa factores normativos NEC utilizados
para ajustar la ampacidad de conductores.

Responsabilidades:

    - corrección por temperatura ambiente
    - corrección por agrupamiento (CCC)
    - cálculo de ampacidad ajustada

NO realiza:

    - selección de calibre
    - cálculo de caída de voltaje
    - acceso a tablas de conductores

Normativa utilizada:

    NEC 310.15(B)(1)  → Ambient Temperature Correction
    NEC 310.15(C)(1)  → Adjustment Factors for CCC
"""

from __future__ import annotations
from typing import Tuple


# ==========================================================
# REFERENCIAS NORMATIVAS
# ==========================================================

NEC_REFERENCIAS = [
    "NEC 310.15(B)(1) - Ambient Temperature Correction",
    "NEC 310.15(C)(1) - Adjustment Factors for Current-Carrying Conductors",
]


# ==========================================================
# FACTOR TEMPERATURA
# ==========================================================

def factor_temperatura_nec(
    t_amb_c: float,
    columna: str = "75C",
) -> float:
    """
    Factor de corrección por temperatura ambiente.

    Basado en NEC 310.15(B)(1).

    columna:
        "75C" → terminales comunes
        "90C" → THWN-2 / PV Wire
    """

    try:
        t = float(t_amb_c)
    except Exception:
        t = 30.0

    col = str(columna).strip().upper()

    if col not in {"75C", "90C"}:
        col = "75C"

    # Simplificación por tramos

    if col == "75C":

        if t <= 30:
            return 1.00
        if t <= 40:
            return 0.91
        if t <= 50:
            return 0.82
        return 0.71

    # 90°C insulation

    if t <= 30:
        return 1.00
    if t <= 40:
        return 0.91
    if t <= 50:
        return 0.82
    return 0.71


# ==========================================================
# FACTOR CCC (AGRUPAMIENTO)
# ==========================================================

def factor_agrupamiento_ccc(
    ccc: int
) -> float:
    """
    Factor de ajuste por cantidad de conductores portadores
    de corriente (CCC).

    Basado en NEC 310.15(C)(1).
    """

    try:
        n = int(ccc)
    except Exception:
        n = 1

    if n <= 3:
        return 1.00

    if n <= 6:
        return 0.80

    if n <= 9:
        return 0.70

    return 0.50


# ==========================================================
# AMPACIDAD AJUSTADA
# ==========================================================

def ampacidad_ajustada_nec(
    ampacidad_base: float,
    t_amb_c: float,
    ccc: int,
    aplicar: bool = True,
    *,
    columna: str = "75C",
) -> Tuple[float, float, float]:
    """
    Calcula ampacidad ajustada según NEC.

    Fórmula:

        Ampacidad_ajustada =
            Ampacidad_base × f_temp × f_ccc

    Returns
    -------
    (ampacidad_ajustada, factor_temperatura, factor_ccc)
    """

    try:
        amp_base = float(ampacidad_base)
    except Exception:
        amp_base = 0.0

    if amp_base <= 0.0:
        return 0.0, 1.0, 1.0

    if not bool(aplicar):
        return amp_base, 1.0, 1.0

    f_temp = factor_temperatura_nec(t_amb_c, columna=columna)
    f_ccc = factor_agrupamiento_ccc(ccc)

    amp_adj = amp_base * f_temp * f_ccc

    return float(amp_adj), float(f_temp), float(f_ccc)
