from __future__ import annotations

from typing import List


# ==========================================================
# DIAS POR MES (AÑO NORMAL)
# ==========================================================

DIAS_MES = [31,28,31,30,31,30,31,31,30,31,30,31]


# ==========================================================
# AGREGACIÓN HORARIA → MENSUAL
# ==========================================================

def agregar_energia_por_mes(potencia_horaria_kw: List[float]) -> List[float]:
    """
    Convierte serie horaria (8760) en energía mensual.

    Entrada:
        potencia_horaria_kw : lista de 8760 valores

    Salida:
        energia_mensual_kwh : lista de 12 valores
    """

    if len(potencia_horaria_kw) != 8760:
        raise ValueError("Serie horaria debe tener 8760 valores.")

    energia_mensual = []

    idx = 0

    for dias in DIAS_MES:

        horas_mes = dias * 24

        bloque = potencia_horaria_kw[idx : idx + horas_mes]

        energia_mes = sum(bloque)

        energia_mensual.append(energia_mes)

        idx += horas_mes

    return energia_mensual
