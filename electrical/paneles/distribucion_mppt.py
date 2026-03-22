from __future__ import annotations

"""
DISTRIBUCIÓN DE STRINGS ENTRE MPPT — FV ENGINE

Define cómo se reparten los strings entre los MPPT.

NO usa dict
SOLO usa dataclass
"""

from dataclasses import dataclass
from typing import List


# ==========================================================
# MODELO TIPADO
# ==========================================================

@dataclass(frozen=True)
class MPPTConfig:
    mppt: int
    n_strings: int


# ==========================================================
# DISTRIBUCIÓN
# ==========================================================

def distribuir_strings(
    strings_totales: int,
    mppts: int
) -> List[int]:

    if strings_totales <= 0:
        return []

    if mppts <= 0:
        raise ValueError("mppts inválido (<=0)")

    base = strings_totales // mppts
    extra = strings_totales % mppts

    return [
        base + (1 if i < extra else 0)
        for i in range(mppts)
    ]


# ==========================================================
# CONFIGURACIÓN MPPT
# ==========================================================

def crear_circuitos_mppt(
    strings_totales: int,
    mppts: int
) -> List[MPPTConfig]:

    distribucion = distribuir_strings(strings_totales, mppts)

    return [
        MPPTConfig(
            mppt=i + 1,
            n_strings=n
        )
        for i, n in enumerate(distribucion)
        if n > 0
    ]


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# distribuir_strings(strings_totales, mppts)
#
# Entrada:
#   strings_totales : int
#   mppts : int
#
# Salida:
#   List[int]
#       → número de strings por MPPT
#
#
# crear_circuitos_mppt(strings_totales, mppts)
#
# Entrada:
#   strings_totales : int
#   mppts : int
#
# Salida:
#   List[MPPTConfig]
#
#   MPPTConfig:
#       mppt       → índice MPPT
#       n_strings  → strings asignados
#
#
# Ubicación:
#   electrical/paneles/
#
# Rol:
#   Distribución topológica del sistema FV
#
#
# Flujo:
#
# calcular_strings_fv
#       ↓
# distribución MPPT (este módulo)
#       ↓
# ResultadoPaneles
#
#
# Regla:
#   NO usar dict
#   NO lógica eléctrica
#   SOLO topología
#
# ==========================================================
