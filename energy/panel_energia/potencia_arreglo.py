"""
MODELO DE ARREGLO FV (ARRAY) — FV Engine

Dominio: electrical.paneles.energia

Responsabilidad
---------------
Calcular los parámetros eléctricos del generador fotovoltaico
completo a partir de los parámetros eléctricos de un string.

Este módulo representa el nivel superior del generador DC
antes del inversor.

Relación en el motor FV
-----------------------

    irradiancia / clima
            ↓
    modelo_termico
            ↓
    potencia_panel
            ↓
    potencia_string
            ↓
    potencia_arreglo      ← ESTE MÓDULO
            ↓
    modelo_inversor
            ↓
    producción energética

Conceptos eléctricos utilizados
-------------------------------

Strings conectados en paralelo forman el generador FV.

Reglas:

    Voltaje del arreglo ≈ voltaje del string
    Corriente del arreglo = suma de corrientes de strings

Por lo tanto:

    V_array ≈ V_string
    I_array = I_string × N_strings

La potencia total del arreglo es:

    P_array = V_array × I_array
"""

from dataclasses import dataclass


# =========================================================
# ENTRADA
# =========================================================

@dataclass
class PotenciaArregloInput:
    """
    Parámetros de entrada del modelo del arreglo FV.
    """

    # configuración física
    n_strings_total: int

    # parámetros del string
    vmp_string_v: float
    voc_string_v: float

    imp_string_a: float
    isc_string_a: float

    potencia_string_w: float


# =========================================================
# SALIDA
# =========================================================

@dataclass
class PotenciaArregloResultado:
    """
    Resultado del comportamiento eléctrico del generador FV.
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

    Parámetros
    ----------
    inp : PotenciaArregloInput
        Parámetros eléctricos del string y número total de strings.

    Retorna
    -------
    PotenciaArregloResultado
        Parámetros eléctricos del generador FV.
    """

    # -----------------------------------------------------
    # Validación básica
    # -----------------------------------------------------

    if inp.n_strings_total <= 0:
        raise ValueError("n_strings_total inválido")

    # -----------------------------------------------------
    # Voltajes del arreglo
    # -----------------------------------------------------
    # En paralelo el voltaje se mantiene
    # -----------------------------------------------------

    vdc_array = inp.vmp_string_v
    voc_array = inp.voc_string_v

    # -----------------------------------------------------
    # Corrientes del arreglo
    # -----------------------------------------------------
    # En paralelo las corrientes se suman
    # -----------------------------------------------------

    idc_array = inp.imp_string_a * inp.n_strings_total
    isc_array = inp.isc_string_a * inp.n_strings_total

    # -----------------------------------------------------
    # Potencia del arreglo
    # -----------------------------------------------------

    potencia_array = inp.potencia_string_w * inp.n_strings_total

    # -----------------------------------------------------
    # Resultado
    # -----------------------------------------------------

    return PotenciaArregloResultado(

        vdc_array_v=vdc_array,
        voc_array_v=voc_array,

        idc_array_a=idc_array,
        isc_array_a=isc_array,

        potencia_array_w=potencia_array
    )
