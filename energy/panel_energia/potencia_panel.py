from __future__ import annotations

"""
MODELO DE POTENCIA DEL PANEL FV — FV Engine

Dominio: paneles / energía

Responsabilidad
---------------
Calcular el comportamiento eléctrico del módulo fotovoltaico
en condiciones reales de operación.

Este módulo ajusta:

• potencia del módulo (Pmp)
• voltaje en punto de máxima potencia (Vmp)
• voltaje en circuito abierto (Voc)
• corriente en MPP (Imp)
• corriente de cortocircuito (Isc)

en función de:

• irradiancia incidente (POA)
• temperatura de celda
• coeficientes térmicos del panel

Modelo utilizado
----------------
Modelo físico simplificado basado en:

    - irradiancia relativa (G/1000)
    - coeficientes térmicos lineales

Este modelo es consistente con simuladores tipo PVsyst (nivel básico).
"""

from dataclasses import dataclass


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass(frozen=True)
class PotenciaPanelInput:
    """
    Parámetros de entrada del modelo del panel FV.
    """

    # ------------------------------------------------------
    # CONDICIONES OPERATIVAS
    # ------------------------------------------------------

    irradiancia_poa_wm2: float
    temperatura_celda_c: float

    # ------------------------------------------------------
    # PARÁMETROS DEL PANEL (referencia nominal)
    # ------------------------------------------------------

    p_panel_w: float

    vmp_panel_v: float
    voc_panel_v: float

    imp_panel_a: float
    isc_panel_a: float

    # ------------------------------------------------------
    # COEFICIENTES TÉRMICOS (1/°C)
    # ------------------------------------------------------

    coef_potencia: float
    coef_vmp: float
    coef_voc: float


@dataclass(frozen=True)
class PotenciaPanelResultado:
    """
    Resultado del comportamiento eléctrico del panel FV.
    """

    pmp_w: float

    vmp_v: float
    voc_v: float

    imp_a: float
    isc_a: float


# ==========================================================
# MOTOR DEL PANEL
# ==========================================================

def calcular_potencia_panel(inp: PotenciaPanelInput) -> PotenciaPanelResultado:
    """
    Calcula el comportamiento eléctrico del panel FV bajo
    condiciones reales de irradiancia y temperatura.

    Modelo:
        - Escalamiento por irradiancia
        - Corrección térmica lineal
        - Consistencia eléctrica: Pmp = Vmp * Imp
    """

    poa = inp.irradiancia_poa_wm2
    t_cell = inp.temperatura_celda_c

    # ------------------------------------------------------
    # SIN IRRADIANCIA → NO GENERACIÓN
    # ------------------------------------------------------

    if poa <= 0:
        return PotenciaPanelResultado(
            pmp_w=0.0,
            vmp_v=0.0,
            voc_v=0.0,
            imp_a=0.0,
            isc_a=0.0,
        )

    # ------------------------------------------------------
    # IRRADIANCIA RELATIVA
    # ------------------------------------------------------

    g_rel = poa / 1000.0

    # ------------------------------------------------------
    # DELTA TÉRMICO
    # ------------------------------------------------------

    delta_t = t_cell - 25.0

    # ------------------------------------------------------
    # VOLTAJE MPP
    # ------------------------------------------------------

    vmp = inp.vmp_panel_v * (1 + inp.coef_vmp * delta_t)

    # ------------------------------------------------------
    # VOLTAJE VOC
    # ------------------------------------------------------

    voc = inp.voc_panel_v * (1 + inp.coef_voc * delta_t)

    # ------------------------------------------------------
    # CORRIENTES
    # ------------------------------------------------------

    imp = inp.imp_panel_a * g_rel
    isc = inp.isc_panel_a * g_rel

    # ------------------------------------------------------
    # POTENCIA CONSISTENTE
    # ------------------------------------------------------

    pmp = vmp * imp
    pmp = max(0.0, pmp)

    # ------------------------------------------------------
    # RESULTADO
    # ------------------------------------------------------

    return PotenciaPanelResultado(
        pmp_w=pmp,
        vmp_v=vmp,
        voc_v=voc,
        imp_a=imp,
        isc_a=isc,
    )
