"""
MODELO DE STRING FV — FV Engine

Dominio: electrical.paneles

Responsabilidad
---------------
Calcular los parámetros eléctricos del string FV a partir de
las características del panel.

Este módulo sirve como puente entre el modelo físico del panel
y el contrato oficial del dominio paneles (StringFV).
"""

from dataclasses import dataclass


# =========================================================
# ENTRADA
# =========================================================

@dataclass
class PotenciaStringInput:

    # configuración física
    n_series: int
    n_strings: int

    # parámetros del panel
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

    vmp_string_v: float
    voc_string_v: float

    imp_string_a: float
    isc_panel_a: float

    potencia_string_w: float

    i_mppt_a: float


# =========================================================
# MOTOR
# =========================================================

def calcular_potencia_string(inp: PotenciaStringInput) -> PotenciaStringResultado:

    # -----------------------------------------------------
    # Voltajes (serie)
    # -----------------------------------------------------

    vmp_string = inp.vmp_panel_v * inp.n_series
    voc_string = inp.voc_panel_v * inp.n_series

    # -----------------------------------------------------
    # Corrientes (no cambian en serie)
    # -----------------------------------------------------

    imp_string = inp.imp_panel_a
    isc_panel = inp.isc_panel_a

    # -----------------------------------------------------
    # Potencia del string
    # -----------------------------------------------------

    potencia_string = inp.p_panel_w * inp.n_series

    # -----------------------------------------------------
    # Corriente total hacia el MPPT
    # -----------------------------------------------------

    i_mppt = imp_string * inp.n_strings

    # -----------------------------------------------------
    # Resultado
    # -----------------------------------------------------

    return PotenciaStringResultado(

        vmp_string_v=vmp_string,
        voc_string_v=voc_string,

        imp_string_a=imp_string,
        isc_panel_a=isc_panel,

        potencia_string_w=potencia_string,

        i_mppt_a=i_mppt
    )
