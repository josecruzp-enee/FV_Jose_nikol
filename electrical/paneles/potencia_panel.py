"""
MODELO DE POTENCIA DEL PANEL FV — FV Engine

Dominio: panel

Responsabilidad
---------------
Calcular el comportamiento eléctrico del módulo fotovoltaico
en condiciones reales de operación.

Este módulo ajusta:

• Voc
• Vmp
• Potencia del módulo

en función de:

• irradiancia incidente (POA)
• temperatura de celda
• coeficientes del panel

Modelo utilizado
----------------
Modelo simplificado basado en coeficientes térmicos.
"""

from dataclasses import dataclass


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass
class PotenciaPanelInput:
    """
    Parámetros de entrada del modelo del panel
    """

    irradiancia_poa_wm2: float
    temperatura_celda_c: float

    pmax_stc_w: float
    vmp_stc_v: float
    voc_stc_v: float

    coef_pmax_pct_per_c: float
    coef_voc_pct_per_c: float
    coef_vmp_pct_per_c: float


@dataclass
class PotenciaPanelResultado:
    """
    Resultado del comportamiento del panel
    """

    pmp_w: float
    vmp_v: float
    voc_v: float


# ==========================================================
# MOTOR DEL PANEL
# ==========================================================

def calcular_potencia_panel(inp: PotenciaPanelInput) -> PotenciaPanelResultado:
    """
    Calcula potencia y voltajes del panel en condiciones reales.
    """

    g = inp.irradiancia_poa_wm2
    t_cell = inp.temperatura_celda_c

    # irradiancia relativa
    g_rel = g / 1000

    # diferencia respecto a STC
    delta_t = t_cell - 25

    # ------------------------------------------------------
    # ajuste de potencia
    # ------------------------------------------------------

    pmp = (
        inp.pmax_stc_w
        * g_rel
        * (1 + inp.coef_pmax_pct_per_c * delta_t)
    )

    # ------------------------------------------------------
    # ajuste de voltaje MPP
    # ------------------------------------------------------

    vmp = (
        inp.vmp_stc_v
        * (1 + inp.coef_vmp_pct_per_c * delta_t)
    )

    # ------------------------------------------------------
    # ajuste de Voc
    # ------------------------------------------------------

    voc = (
        inp.voc_stc_v
        * (1 + inp.coef_voc_pct_per_c * delta_t)
    )

    return PotenciaPanelResultado(
        pmp_w=pmp,
        vmp_v=vmp,
        voc_v=voc
    )
