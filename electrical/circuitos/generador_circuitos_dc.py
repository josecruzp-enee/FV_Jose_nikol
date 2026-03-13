"""
Motor de generación de circuitos DC — FV Engine

FRONTERA DEL MÓDULO
-------------------
Este módulo construye la topología DC entre strings y MPPT.

Flujo interno:
Entradas → Validación → Distribución → Salida

Responsabilidades:
- distribuir strings entre MPPT

NO realiza:
- cálculo de corrientes
- cálculo NEC
- dimensionamiento de conductores
- dimensionamiento de protecciones
"""

from __future__ import annotations
from typing import Dict, List

from electrical.paneles.distribucion_mppt import distribuir_strings


# ==========================================================
# GENERACIÓN DE CIRCUITOS DC
# ==========================================================

def generar_circuitos_dc(
    strings_totales: int,
    mppts: int,
) -> List[Dict[str, int]]:

    if strings_totales <= 0:
        raise ValueError("strings_totales inválido")

    if mppts <= 0:
        raise ValueError("mppts inválido")

    distribucion = distribuir_strings(strings_totales, mppts)

    circuitos: List[Dict[str, int]] = []

    for i, n_strings in enumerate(distribucion):

        circuito = {
            "mppt": i + 1,
            "strings": int(n_strings),
        }

        circuitos.append(circuito)

    return circuitos
