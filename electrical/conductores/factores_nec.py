"""
factores_nec.py — FV Engine

Factores de corrección NEC 2023 para ampacidad de conductores.

Base normativa:
- NEC 310.15(B)(1) → Corrección por temperatura ambiente.
- NEC 310.15(C)(1) → Ajuste por agrupamiento de conductores (CCC).

Objetivo:
Aplicar derating normativo sin modificar el modelo físico del conductor.
"""

# Referencias normativas utilizadas en este módulo
NEC_REFERENCIAS = [
    "NEC 310.15(B)(1) - Ambient Temperature Correction",
    "NEC 310.15(C)(1) - Adjustment Factors for Current-Carrying Conductors",
]


# Calcula el factor de corrección por temperatura ambiente según NEC 310.15(B)(1).
def factor_temperatura_nec(t_amb_c: float, columna: str = "75C") -> float:
    """
    Usa valores simplificados para columna 75°C
    (terminales típicas THWN-2 / equipos ≤100A).
    """

    if t_amb_c <= 30:
        return 1.00
    if t_amb_c <= 40:
        return 0.91
    if t_amb_c <= 50:
        return 0.82
    return 0.71


# Calcula el factor de ajuste por cantidad de conductores portadores de corriente (CCC).
def factor_agrupamiento_ccc(ccc: int) -> float:
    """
    NEC 310.15(C)(1)

    Reduce ampacidad cuando múltiples conductores
    comparten la misma canalización.
    """

    if ccc <= 3:
        return 1.00
    if ccc <= 6:
        return 0.80
    if ccc <= 9:
        return 0.70
    return 0.50


# Aplica el ajuste completo NEC a una ampacidad base del conductor.
def ampacidad_ajustada_nec(
    ampacidad_base: float,
    t_amb_c: float,
    ccc: int,
    aplicar: bool = True,
):
    """
    NEC 310.15(B)(1) + 310.15(C)(1)

    Ampacidad_final =
        Ampacidad_base × Factor_temperatura × Factor_CCC

    Returns:
        ampacidad_ajustada (A)
        factor_temperatura
        factor_ccc
    """

    # Permite comparar cálculos con y sin derating
    if not aplicar:
        return ampacidad_base, 1.0, 1.0

    f_temp = factor_temperatura_nec(t_amb_c)
    f_ccc = factor_agrupamiento_ccc(ccc)

    ampacidad_ajustada = ampacidad_base * f_temp * f_ccc

    return ampacidad_ajustada, f_temp, f_ccc
