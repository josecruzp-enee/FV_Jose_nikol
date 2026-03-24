from typing import List
import math


def agregar_energia_por_mes(serie_kw: List[float]) -> List[float]:
    """
    Convierte una serie horaria (8760 o 8784) en energía mensual (kWh).

    Asume:
    - Paso de tiempo = 1 hora
    - Potencia en kW → energía en kWh por suma directa
    """

    n = len(serie_kw)

    if n not in (8760, 8784):
        raise ValueError("Serie inválida: debe ser 8760 o 8784 horas")

    # Validación de valores
    for v in serie_kw:
        if not math.isfinite(v):
            raise ValueError("Serie contiene NaN o infinito")
        if v < 0:
            raise ValueError("Serie contiene valores negativos")

    # Calendario
    if n == 8784:
        dias_mes = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else:
        dias_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    energia_mensual = []
    idx = 0

    for dias in dias_mes:
        horas_mes = dias * 24

        bloque = serie_kw[idx: idx + horas_mes]
        energia_mes = sum(bloque)

        energia_mensual.append(energia_mes)
        idx += horas_mes

    if idx != n:
        raise ValueError("Error en agregación mensual: desfase de horas")

    return energia_mensual
