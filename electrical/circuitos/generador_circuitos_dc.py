"""
Motor de generación de circuitos DC — FV Engine

FRONTERA DEL MÓDULO
-------------------
Este módulo se encarga de construir los circuitos DC que llegan
a los MPPT del inversor a partir del número total de strings.

Flujo interno:
    Entradas → Validación → Distribución → Cálculo → Salida

Responsabilidades:
    - distribuir strings entre MPPT
    - calcular corriente de operación
    - calcular corriente de diseño NEC (690.8)

NO realiza:
    - cálculo de caída de voltaje
    - selección de conductores
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
    isc_string: float,
    factor_nec: float = 1.25,
) -> List[Dict[str, float]]:
    """
    Genera los circuitos DC conectados a los MPPT del inversor.

    Parámetros
    ----------
    strings_totales : int
        Número total de strings del sistema.

    mppts : int
        Número de MPPT del inversor.

    isc_string : float
        Corriente de cortocircuito de un string (A).

    factor_nec : float
        Factor NEC para corriente de diseño.
        Default = 1.25 (NEC 690.8).

    Retorna
    -------
    List[Dict]

    Cada elemento representa un circuito DC conectado a un MPPT.

    Estructura:

    {
        "mppt": int                # número de MPPT
        "strings": int             # strings conectados
        "i_operacion_a": float     # corriente de operación
        "i_diseno_nec_a": float    # corriente de diseño NEC
    }
    """

    # ======================================================
    # VALIDACIÓN DE ENTRADAS
    # ======================================================

    if strings_totales <= 0:
        raise ValueError("strings_totales inválido")

    if mppts <= 0:
        raise ValueError("mppts inválido")

    if isc_string <= 0:
        raise ValueError("isc_string inválido")

    if factor_nec <= 0:
        raise ValueError("factor_nec inválido")

    # ======================================================
    # DISTRIBUCIÓN DE STRINGS EN MPPT
    # ======================================================

    distribucion = distribuir_strings(strings_totales, mppts)

    # ======================================================
    # CÁLCULO DE CORRIENTES
    # ======================================================

    circuitos: List[Dict[str, float]] = []

    for i, n_strings in enumerate(distribucion):

        # corriente de operación
        i_oper = n_strings * isc_string

        # corriente de diseño NEC
        i_dis = i_oper * factor_nec

        circuito = {
            "mppt": i + 1,
            "strings": int(n_strings),

            "i_operacion_a": float(i_oper),
            "i_diseno_nec_a": float(i_dis),
        }

        circuitos.append(circuito)

    # ======================================================
    # SALIDA
    # ======================================================

    return circuitos
