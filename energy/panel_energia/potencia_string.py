from __future__ import annotations

"""
MODELO DE STRING FV — FV Engine

Dominio: paneles / energía

Responsabilidad
---------------
Calcular los parámetros eléctricos de UN string fotovoltaico
(paneles conectados en serie).

Este módulo NO considera conexiones en paralelo ni MPPT.

Relación en el motor FV
-----------------------

    clima / irradiancia
            ↓
    modelo_termico
            ↓
    potencia_panel
            ↓
    potencia_string   ← ESTE MÓDULO (solo serie)
            ↓
    potencia_arreglo  (paralelo)
"""

from dataclasses import dataclass


# =========================================================
# ENTRADA
# =========================================================

@dataclass(frozen=True)
class PotenciaStringInput:
    """
    Parámetros de entrada del modelo del string FV.
    """

    # -----------------------------------------------------
    # CONFIGURACIÓN (SERIE)
    # -----------------------------------------------------

    n_series: int

    # -----------------------------------------------------
    # PARÁMETROS DEL PANEL
    # -----------------------------------------------------

    p_panel_w: float

    vmp_panel_v: float
    voc_panel_v: float

    imp_panel_a: float
    isc_panel_a: float


# =========================================================
# SALIDA
# =========================================================

@dataclass(frozen=True)
class PotenciaStringResultado:
    """
    Resultado eléctrico de UN string FV.
    """

    vmp_string_v: float
    voc_string_v: float

    imp_string_a: float
    isc_string_a: float

    potencia_string_w: float


# =========================================================
# MOTOR
# =========================================================

def calcular_potencia_string(inp: PotenciaStringInput) -> PotenciaStringResultado:
    """
    Calcula los parámetros eléctricos de un string FV
    (paneles en serie).

    Modelo:

        V_string = V_panel * N_series
        I_string = I_panel
        P_string = V_string * I_string
    """

    # -----------------------------------------------------
    # VALIDACIONES
    # -----------------------------------------------------

    if inp.n_series <= 0:
        raise ValueError("n_series inválido")

    # -----------------------------------------------------
    # VOLTAJES (serie)
    # -----------------------------------------------------

    vmp_string = inp.vmp_panel_v * inp.n_series
    voc_string = inp.voc_panel_v * inp.n_series

    # -----------------------------------------------------
    # CORRIENTES (serie)
    # -----------------------------------------------------

    imp_string = inp.imp_panel_a
    isc_string = inp.isc_panel_a

    # -----------------------------------------------------
    # POTENCIA CONSISTENTE
    # -----------------------------------------------------

    potencia_string = vmp_string * imp_string

    # -----------------------------------------------------
    # RESULTADO
    # -----------------------------------------------------

    return PotenciaStringResultado(
        vmp_string_v=vmp_string,
        voc_string_v=voc_string,
        imp_string_a=imp_string,
        isc_string_a=isc_string,
        potencia_string_w=potencia_string,
    )
