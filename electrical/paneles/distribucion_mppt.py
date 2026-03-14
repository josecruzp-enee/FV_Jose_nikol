from __future__ import annotations

"""
DISTRIBUCIÓN DE STRINGS ENTRE MPPT — FV ENGINE
==============================================

Este módulo define la configuración de conexión de strings
del generador fotovoltaico hacia los MPPT del inversor.

Responsabilidad
---------------

Determinar cómo se distribuyen los strings del generador FV
entre los diferentes MPPT disponibles en el inversor.

Este módulo SOLO calcula la topología de conexión.

NO calcula:

    - corrientes
    - voltajes
    - límites eléctricos
    - normativa NEC
    - dimensionamiento eléctrico

Estos cálculos pertenecen a otros dominios.

----------------------------------------------------------
ENTRADAS
----------------------------------------------------------

strings_totales : int
    número total de strings del generador FV

mppts : int
    número de MPPT disponibles en el inversor


----------------------------------------------------------
SALIDA
----------------------------------------------------------

Configuración de strings por MPPT.

Ejemplo:

    strings_totales = 10
    mppts = 3

Resultado:

    [4, 3, 3]

Significa:

    MPPT1 → 4 strings
    MPPT2 → 3 strings
    MPPT3 → 3 strings
"""

from typing import List, Dict


# ==========================================================
# DISTRIBUCIÓN DE STRINGS ENTRE MPPT
# ==========================================================

def distribuir_strings(
    strings_totales: int,
    mppts: int
) -> List[int]:
    """
    Calcula una distribución balanceada de strings entre MPPT.
    """

    if strings_totales <= 0:
        return []

    if mppts <= 0:
        raise ValueError("mppts inválido (<=0)")

    base = strings_totales // mppts
    extra = strings_totales % mppts

    distribucion: List[int] = []

    for i in range(mppts):

        n = base

        # los primeros MPPT reciben un string adicional si sobran
        if i < extra:
            n += 1

        distribucion.append(n)

    return distribucion


# ==========================================================
# CREACIÓN DE CONFIGURACIÓN MPPT
# ==========================================================

def crear_circuitos_mppt(
    strings_totales: int,
    mppts: int
) -> List[Dict]:
    """
    Genera la configuración de strings conectados a cada MPPT.
    """

    distribucion = distribuir_strings(
        strings_totales,
        mppts
    )

    circuitos: List[Dict] = []

    for i, n in enumerate(distribucion):

        # si un MPPT no recibe strings se ignora
        if n == 0:
            continue

        circuitos.append({

            "mppt": i + 1,
            "strings": n

        })

    return circuitos


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================

"""
Funciones exportadas por este módulo:

distribuir_strings(strings_totales, mppts)

    devuelve:
        [n_strings_mppt1, n_strings_mppt2, ...]


crear_circuitos_mppt(strings_totales, mppts)

    devuelve:

    [
        {
            "mppt": int,
            "strings": int
        }
    ]


Consumido por:

    electrical.paneles.orquestador_paneles
"""
