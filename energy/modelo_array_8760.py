from __future__ import annotations

"""
MODELO DEL ARREGLO FV (SIMULACIÓN 8760) — FV Engine

Dominio
-------
electrical.paneles

Responsabilidad
---------------
Calcular la potencia DC del generador fotovoltaico
para cada hora del año a partir de:

• condiciones solares (POA)
• temperatura de celda
• configuración eléctrica del generador

Este módulo NO calcula:

• posición solar
• irradiancia
• temperatura de celda
• clipping del inversor
• pérdidas AC

Esas responsabilidades pertenecen a otros módulos.

Flujo dentro del motor energético
---------------------------------

EstadoSolarHora (simulación 8760)
        ↓
potencia_panel
        ↓
potencia_string
        ↓
potencia_arreglo   ← ESTE MÓDULO
        ↓
potencia DC horaria del sistema

Salida
------
Serie horaria de potencia DC del arreglo FV.
"""

from dataclasses import dataclass
from typing import List

from electrical.paneles.potencia_panel import (
    calcular_potencia_panel,
    PotenciaPanelInput,
)

from energy.clima.simulacion_8760 import EstadoSolarHora


# ==========================================================
# ENTRADA DEL MODELO
# ==========================================================

@dataclass
class Array8760Input:
    """
    Parámetros necesarios para simular el arreglo FV.
    """

    estado_solar: List[EstadoSolarHora]

    # Configuración eléctrica
    paneles_por_string: int
    strings_totales: int

    # Parámetros eléctricos del panel (STC)
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
    """
    Potencia DC horaria del generador FV.
    """

    potencia_dc_kw: List[float]


# ==========================================================
# MOTOR DEL ARREGLO
# ==========================================================

def calcular_array_8760(inp: Array8760Input) -> Array8760Resultado:
    """
    Calcula la potencia DC del arreglo fotovoltaico
    para cada hora del año (8760).
    """

    potencia_dc_kw: List[float] = []

    # ======================================================
    # SIMULACIÓN HORARIA
    # ======================================================

    for hora in inp.estado_solar:

        # --------------------------------------------------
        # MODELO DEL PANEL
        # --------------------------------------------------

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

        # --------------------------------------------------
        # POTENCIA DEL STRING
        # --------------------------------------------------

        potencia_string_w = panel.pmp_w * inp.paneles_por_string

        # --------------------------------------------------
        # POTENCIA DEL ARREGLO
        # --------------------------------------------------

        potencia_array_w = potencia_string_w * inp.strings_totales

        # --------------------------------------------------
        # CONVERTIR A kW
        # --------------------------------------------------

        potencia_dc_kw.append(potencia_array_w / 1000)

    # ======================================================
    # RESULTADO
    # ======================================================

    return Array8760Resultado(

        potencia_dc_kw=potencia_dc_kw

    )
