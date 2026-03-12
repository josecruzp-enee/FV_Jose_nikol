from __future__ import annotations

from typing import List, Dict


# ==========================================================
# DISTRIBUCION DE STRINGS ENTRE MPPT
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

    distribucion: List[int] = []

    for i in range(mppts):

        n = base

        if i < extra:
            n += 1

        distribucion.append(n)

    return distribucion


# ==========================================================
# CREACION DE CIRCUITOS MPPT
# ==========================================================

def crear_circuitos_mppt(
    strings_totales: int,
    mppts: int,
    imp_string: float
) -> List[Dict]:

    distribucion = distribuir_strings(
        strings_totales,
        mppts
    )

    circuitos: List[Dict] = []

    for i, n in enumerate(distribucion):

        if n == 0:
            continue

        i_oper = float(n) * float(imp_string)

        # NEC 690.8
        i_dis = i_oper * 1.25

        circuitos.append({

            "mppt": i + 1,

            "strings": n,

            "i_operacion": i_oper,

            "i_diseno": i_dis

        })

    return circuitos


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# distribuir_strings(strings_totales, mppts)
#
# devuelve:
#   [n_strings_mppt1, n_strings_mppt2, ...]
#
#
# crear_circuitos_mppt(strings_totales, mppts, imp_string)
#
# devuelve:
#
# [
#   {
#     "mppt": int,
#     "strings": int,
#     "i_operacion": float,
#     "i_diseno": float
#   }
# ]
#
# Consumido por:
# electrical.paneles.orquestador_paneles
#
# ==========================================================
