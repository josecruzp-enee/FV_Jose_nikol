"""
factores_nec.py
---------------------------------------------------------
Factores de corrección NEC 2023 para ampacidad de conductores.

Diseñado como capa adicional SIN modificar la arquitectura
existente del motor eléctrico FV.

Aplica:
- Corrección por temperatura ambiente (NEC 310.15)
- Ajuste por agrupamiento de conductores CCC
---------------------------------------------------------
"""


# ---------------------------------------------------------
# FACTOR TEMPERATURA (NEC 310.15)
# Valores simplificados para columna 75°C (THWN-2 / terminales típicas)
# Luego podrás reemplazar por tabla completa.
# ---------------------------------------------------------
def factor_temperatura_nec(t_amb_c: float, columna: str = "75C") -> float:
    """
    Retorna factor de corrección por temperatura ambiente.
    """
    if t_amb_c <= 30:
        return 1.00
    if t_amb_c <= 40:
        return 0.91
    if t_amb_c <= 50:
        return 0.82
    return 0.71


# ---------------------------------------------------------
# FACTOR AGRUPAMIENTO (CCC)
# NEC 310.15(C)(1)
# ---------------------------------------------------------
def factor_agrupamiento_ccc(ccc: int) -> float:
    """
    Retorna factor de ajuste por cantidad de conductores
    portadores de corriente dentro del mismo ducto.
    """
    if ccc <= 3:
        return 1.00
    if ccc <= 6:
        return 0.80
    if ccc <= 9:
        return 0.70
    return 0.50


# ---------------------------------------------------------
# AMPACIDAD AJUSTADA NEC
# ---------------------------------------------------------
def ampacidad_ajustada_nec(
    ampacidad_base: float,
    t_amb_c: float,
    ccc: int,
    aplicar: bool = True,
):
    """
    Aplica factores NEC a una ampacidad base.

    Returns:
        ampacidad_ajustada (A)
        factor_temperatura
        factor_ccc
    """

    # Feature flag → no rompe cálculos existentes
    if not aplicar:
        return ampacidad_base, 1.0, 1.0

    f_temp = factor_temperatura_nec(t_amb_c)
    f_ccc = factor_agrupamiento_ccc(ccc)

    ampacidad_ajustada = ampacidad_base * f_temp * f_ccc

    return ampacidad_ajustada, f_temp, f_ccc
