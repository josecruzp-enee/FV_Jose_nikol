"""
MODELO DE STRING FV — FV Engine

Dominio: electrical.paneles.energia

Responsabilidad
---------------
Calcular los parámetros eléctricos de un string fotovoltaico
a partir de las características eléctricas de un panel.

Este módulo representa el siguiente nivel físico del sistema
fotovoltaico después del modelo del panel.

Relación en el motor FV
-----------------------

    clima / irradiancia
            ↓
    modelo_termico
            ↓
    potencia_panel
            ↓
    potencia_string      ← ESTE MÓDULO
            ↓
    potencia_arreglo
            ↓
    producción energética del sistema

Conceptos eléctricos utilizados
-------------------------------

Paneles conectados en SERIE:

    • el voltaje se suma
    • la corriente permanece igual

Por lo tanto:

    V_string = V_panel × N_series
    I_string = I_panel

Strings conectados en PARALELO hacia el MPPT:

    • el voltaje permanece igual
    • la corriente se suma

Por lo tanto:

    I_mppt = I_string × N_strings

Este módulo sirve como puente entre el modelo físico del panel
y el contrato oficial del dominio paneles (StringFV).
"""

from dataclasses import dataclass


# =========================================================
# ENTRADA
# =========================================================

@dataclass
class PotenciaStringInput:
    """
    Parámetros de entrada del modelo del string FV.
    """

    # -----------------------------------------------------
    # Configuración física del string
    # -----------------------------------------------------

    n_series: int
    n_strings: int

    # -----------------------------------------------------
    # Parámetros eléctricos del panel
    # -----------------------------------------------------

    p_panel_w: float
    vmp_panel_v: float
    voc_panel_v: float

    imp_panel_a: float
    isc_panel_a: float


# =========================================================
# SALIDA
# =========================================================

@dataclass
class PotenciaStringResultado:
    """
    Resultado del modelo eléctrico del string FV.
    """

    vmp_string_v: float
    voc_string_v: float

    imp_string_a: float
    isc_string_a: float

    potencia_string_w: float

    i_mppt_a: float


# =========================================================
# MOTOR
# =========================================================

def calcular_potencia_string(inp: PotenciaStringInput) -> PotenciaStringResultado:
    """
    Calcula los parámetros eléctricos del string FV
    a partir de las características del panel.

    Parámetros
    ----------
    inp : PotenciaStringInput
        Configuración física del string y parámetros eléctricos
        del panel fotovoltaico.

    Retorna
    -------
    PotenciaStringResultado
        Parámetros eléctricos del string y corriente hacia MPPT.
    """

    # -----------------------------------------------------
    # Validaciones básicas
    # -----------------------------------------------------

    if inp.n_series <= 0:
        raise ValueError("n_series inválido")

    if inp.n_strings <= 0:
        raise ValueError("n_strings inválido")

    # -----------------------------------------------------
    # Voltajes del string (paneles en serie)
    # -----------------------------------------------------

    vmp_string = inp.vmp_panel_v * inp.n_series
    voc_string = inp.voc_panel_v * inp.n_series

    # -----------------------------------------------------
    # Corrientes del string
    # -----------------------------------------------------
    # En serie la corriente no cambia
    # -----------------------------------------------------

    imp_string = inp.imp_panel_a
    isc_string = inp.isc_panel_a

    # -----------------------------------------------------
    # Potencia del string
    # -----------------------------------------------------
    # Potencia eléctrica aproximada en MPP
    # -----------------------------------------------------

    potencia_string = vmp_string * imp_string

    # -----------------------------------------------------
    # Corriente total hacia el MPPT
    # -----------------------------------------------------
    # Strings en paralelo suman corriente
    # -----------------------------------------------------

    i_mppt = imp_string * inp.n_strings

    # -----------------------------------------------------
    # Resultado
    # -----------------------------------------------------

    return PotenciaStringResultado(

        vmp_string_v=vmp_string,
        voc_string_v=voc_string,

        imp_string_a=imp_string,
        isc_string_a=isc_string,

        potencia_string_w=potencia_string,

        i_mppt_a=i_mppt
    )
