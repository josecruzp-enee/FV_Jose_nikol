from __future__ import annotations

"""
MODELO DE ARREGLO FV (ARRAY) — FV Engine

Dominio: paneles / energía

Responsabilidad
---------------
Calcular el comportamiento eléctrico del generador FV completo
a partir de un string fotovoltaico.

Este módulo representa el nivel superior del generador DC
antes del inversor.

Modelo físico:

    Strings en paralelo:

        V_array ≈ V_string
        I_array = I_string × N_strings
        P_array = P_string × N_strings
"""

from dataclasses import dataclass


# =========================================================
# ENTRADA
# =========================================================

@dataclass(frozen=True)
class PotenciaArregloInput:
    """
    Parámetros de entrada del modelo del arreglo FV.
    """

    # -----------------------------------------------------
    # CONFIGURACIÓN (PARALELO)
    # -----------------------------------------------------

    n_strings_total: int

    # -----------------------------------------------------
    # PARÁMETROS DEL STRING
    # -----------------------------------------------------

    vmp_string_v: float
    voc_string_v: float

    imp_string_a: float
    isc_string_a: float

    potencia_string_w: float


# =========================================================
# SALIDA
# =========================================================

@dataclass(frozen=True)
class PotenciaArregloResultado:
    """
    Resultado eléctrico del generador FV completo.
    """

    vdc_array_v: float
    voc_array_v: float

    idc_array_a: float
    isc_array_a: float

    potencia_array_w: float


# =========================================================
# MOTOR
# =========================================================

def calcular_potencia_arreglo(inp: PotenciaArregloInput) -> PotenciaArregloResultado:
    """
    Calcula los parámetros eléctricos del generador FV completo.

    Modelo:

        V_array = V_string
        I_array = I_string × N_strings
        P_array = P_string × N_strings
    """

    # -----------------------------------------------------
    # VALIDACIÓN
    # -----------------------------------------------------

    if inp.n_strings_total <= 0:
        raise ValueError("n_strings_total inválido")

    # -----------------------------------------------------
    # VOLTAJE (paralelo → no cambia)
    # -----------------------------------------------------

    vdc_array = inp.vmp_string_v
    voc_array = inp.voc_string_v

    # -----------------------------------------------------
    # CORRIENTE (paralelo → suma)
    # -----------------------------------------------------

    idc_array = inp.imp_string_a * inp.n_strings_total
    isc_array = inp.isc_string_a * inp.n_strings_total

    # -----------------------------------------------------
    # POTENCIA (consistente con modelo previo)
    # -----------------------------------------------------

    potencia_array = inp.potencia_string_w * inp.n_strings_total

    # -----------------------------------------------------
    # RESULTADO
    # -----------------------------------------------------

    return PotenciaArregloResultado(
        vdc_array_v=vdc_array,
        voc_array_v=voc_array,

        idc_array_a=idc_array,
        isc_array_a=isc_array,

        potencia_array_w=potencia_array,
    )
