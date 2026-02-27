"""
factores_nec.py — FV Engine

Factores de corrección NEC (simplificados) para ampacidad de conductores.

Base normativa:
- NEC 310.15(B)(1) → Corrección por temperatura ambiente.
- NEC 310.15(C)(1) → Ajuste por agrupamiento de conductores (CCC).

Objetivo:
Aplicar derating normativo sin modificar el modelo físico del conductor.
"""

from __future__ import annotations

from typing import Tuple

# Referencias normativas utilizadas en este módulo
NEC_REFERENCIAS = [
    "NEC 310.15(B)(1) - Ambient Temperature Correction",
    "NEC 310.15(C)(1) - Adjustment Factors for Current-Carrying Conductors",
]


def factor_temperatura_nec(t_amb_c: float, columna: str = "75C") -> float:
    """
    Factor de corrección por temperatura ambiente (NEC 310.15(B)(1)).

    Implementación simplificada por columna de temperatura del aislamiento:
    - '75C': terminales típicas / equipos ≤100A (muy común en diseño).
    - '90C': aislamiento 90°C (ej. THWN-2, PV Wire). *Ojo*: terminal puede limitar.

    Nota: estos valores son aproximados (tabla real es más granular).
    """
    try:
        t = float(t_amb_c)
    except Exception:
        t = 30.0

    col = str(columna).strip().upper()
    if col not in {"75C", "90C"}:
        col = "75C"

    # Simplificación por tramos (referencial)
    # 75C (aprox)
    if col == "75C":
        if t <= 30:
            return 1.00
        if t <= 40:
            return 0.91
        if t <= 50:
            return 0.82
        return 0.71

    # 90C (aprox)
    # (valores típicamente menos severos que 75C)
    if t <= 30:
        return 1.00
    if t <= 40:
        return 0.91  # puedes refinar después (ej. 0.91/0.94 según tabla real)
    if t <= 50:
        return 0.82
    return 0.71


def factor_agrupamiento_ccc(ccc: int) -> float:
    """
    Factor de ajuste por cantidad de conductores portadores de corriente (CCC).
    NEC 310.15(C)(1), simplificado.

    ccc:
      - 1–3  -> 1.00
      - 4–6  -> 0.80
      - 7–9  -> 0.70
      - >=10 -> 0.50 (simplificado)
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


def ampacidad_ajustada_nec(
    ampacidad_base: float,
    t_amb_c: float,
    ccc: int,
    aplicar: bool = True,
    *,
    columna: str = "75C",
) -> Tuple[float, float, float]:
    """
    Aplica derating completo:
        Ampacidad_ajustada = Ampacidad_base × f_temp × f_ccc

    Returns:
        (ampacidad_ajustada, f_temp, f_ccc)
    """
    try:
        amp_base = float(ampacidad_base)
    except Exception:
        amp_base = 0.0

    if amp_base <= 0.0:
        return 0.0, 1.0, 1.0

    # Permite comparar cálculos con y sin derating
    if not bool(aplicar):
        return float(amp_base), 1.0, 1.0

    f_temp = float(factor_temperatura_nec(t_amb_c, columna=columna))
    f_ccc = float(factor_agrupamiento_ccc(ccc))

    amp_adj = float(amp_base) * f_temp * f_ccc
    return amp_adj, f_temp, f_ccc
