# -*- coding: utf-8 -*-
from __future__ import annotations


def promediar_energia_8760_a_24h(energia_horaria_kwh):
    """
    Convierte una serie horaria 8760 a perfil promedio 24h.

    Mantiene el mismo corrimiento horario usado en reportes/generar_charts.py:
        hora = (idx - 6) % 24
    """

    if not energia_horaria_kwh:
        return []

    suma = [0.0] * 24
    conteo = [0] * 24

    for idx, valor in enumerate(energia_horaria_kwh):
        hora = (idx - 6) % 24
        suma[hora] += float(valor or 0.0)
        conteo[hora] += 1

    return [
        suma[h] / conteo[h] if conteo[h] else 0.0
        for h in range(24)
    ]
