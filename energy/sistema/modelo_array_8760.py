from __future__ import annotations

"""
MODELO DEL ARREGLO FV (SIMULACIÓN 8760) — FV Engine
"""

from dataclasses import dataclass
from typing import List

from energy.panel_energia.potencia_panel import (
    calcular_potencia_panel,
    PotenciaPanelInput,
)

from energy.clima.simulacion_8760 import EstadoSolarHora


# ==========================================================
# ENTRADA
# ==========================================================

@dataclass
class Array8760Input:

    estado_solar: List[EstadoSolarHora]

    # configuración del generador
    paneles_por_string: int
    strings_totales: int

    # parámetros eléctricos STC
    pmax_stc_w: float
    vmp_stc_v: float
    voc_stc_v: float

    # coeficientes térmicos
    coef_pmax_pct_per_c: float
    coef_voc_pct_per_c: float
    coef_vmp_pct_per_c: float


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass
class Array8760Resultado:

    potencia_dc_kw: List[float]


# ==========================================================
# MOTOR
# ==========================================================

def calcular_array_8760(inp: Array8760Input) -> Array8760Resultado:

    # ------------------------------------------------------
    # VALIDACIÓN
    # ------------------------------------------------------

    if len(inp.estado_solar) == 0:
        raise ValueError("estado_solar está vacío")

    # Si es TMY debería ser 8760
    if len(inp.estado_solar) not in (8760, 8784):
        raise ValueError(
            f"Serie climática inválida: {len(inp.estado_solar)} horas"
        )

    # ------------------------------------------------------
    # PREASIGNACIÓN (más eficiente)
    # ------------------------------------------------------

    n = len(inp.estado_solar)
    potencia_dc_kw = [0.0] * n

    # ------------------------------------------------------
    # SIMULACIÓN HORARIA
    # ------------------------------------------------------

    for i, hora in enumerate(inp.estado_solar):

        # si no hay irradiancia → potencia 0
        if hora.poa_wm2 <= 0:
            potencia_dc_kw[i] = 0.0
            continue

        # ---------------------------------------------
        # POTENCIA DEL PANEL
        # ---------------------------------------------

        panel = calcular_potencia_panel(

            PotenciaPanelInput(

                irradiancia_poa_wm2=hora.poa_wm2,
                temperatura_celda_c=hora.temp_celda_c,

                pmax_stc_w=inp.pmax_stc_w,
                vmp_stc_v=inp.vmp_stc_v,
                voc_stc_v=inp.voc_stc_v,

                coef_pmax_pct_per_c=inp.coef_pmax_pct_per_c,
                coef_voc_pct_per_c=inp.coef_voc_pct_per_c,
                coef_vmp_pct_per_c=inp.coef_vmp_pct_per_c,
            )

        )

        # ---------------------------------------------
        # POTENCIA STRING
        # ---------------------------------------------

        potencia_string_w = panel.pmp_w * inp.paneles_por_string

        # ---------------------------------------------
        # POTENCIA ARREGLO
        # ---------------------------------------------

        potencia_array_w = potencia_string_w * inp.strings_totales

        # protección contra negativos
        potencia_array_w = max(0.0, potencia_array_w)

        # ---------------------------------------------
        # CONVERSIÓN A kW
        # ---------------------------------------------

        potencia_dc_kw[i] = potencia_array_w / 1000.0

    # ------------------------------------------------------
    # RESULTADO
    # ------------------------------------------------------

    return Array8760Resultado(

        potencia_dc_kw=potencia_dc_kw

    )
