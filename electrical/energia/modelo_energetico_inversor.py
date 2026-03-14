from __future__ import annotations

"""
MODELO ENERGÉTICO DEL INVERSOR — FV Engine

Dominio: electrical.energia.inversor

Responsabilidad
---------------
Calcular la producción energética AC del sistema FV
considerando:

• eficiencia del inversor
• pérdidas por clipping DC/AC

Este modelo opera a nivel energético (mensual o anual),
no a nivel eléctrico instantáneo.

Conceptos físicos modelados
---------------------------

1) Conversión energética

    E_AC = E_DC × eficiencia

2) Clipping energético

    Cuando el generador DC es mayor que la capacidad AC
    del inversor (DC/AC ratio > 1), parte de la energía
    generada no puede ser convertida.

Relación en el motor FV
-----------------------

    producción DC del sistema
            ↓
    modelo inversor energético   ← ESTE MÓDULO
            ↓
    producción AC final
"""

from dataclasses import dataclass
from typing import List


Vector12 = List[float]


# ==========================================================
# ENTRADA
# ==========================================================

@dataclass
class EnergiaInversorInput:
    """
    Parámetros energéticos del sistema.
    """

    energia_dc_12m_kwh: Vector12

    pdc_kw: float
    kw_ac: float

    eficiencia: float


# ==========================================================
# SALIDA
# ==========================================================

@dataclass
class EnergiaInversorResultado:
    """
    Resultado energético del inversor.
    """

    energia_ac_12m_kwh: Vector12
    energia_clipping_12m_kwh: Vector12

    energia_ac_anual_kwh: float
    energia_clipping_anual_kwh: float


# ==========================================================
# MOTOR
# ==========================================================

def calcular_energia_inversor(inp: EnergiaInversorInput) -> EnergiaInversorResultado:
    """
    Calcula la energía AC final considerando eficiencia
    y pérdidas por clipping.
    """

    energia_ac: Vector12 = []
    energia_clip: Vector12 = []

    # ------------------------------------------------------
    # DC/AC ratio
    # ------------------------------------------------------

    ratio = inp.pdc_kw / inp.kw_ac if inp.kw_ac > 0 else 1

    loss_clip = 0.0

    if ratio > 1:

        # modelo simplificado de clipping energético
        loss_clip = min(0.15, 0.5 * (ratio - 1) ** 2)

    # ------------------------------------------------------
    # Cálculo mensual
    # ------------------------------------------------------

    for e in inp.energia_dc_12m_kwh:

        # aplicar eficiencia del inversor
        e_ac = e * inp.eficiencia

        # energía recortada por clipping
        recorte = e_ac * loss_clip

        energia_clip.append(recorte)

        energia_ac.append(max(0.0, e_ac - recorte))

    # ------------------------------------------------------
    # Resultado
    # ------------------------------------------------------

    return EnergiaInversorResultado(

        energia_ac_12m_kwh=energia_ac,
        energia_clipping_12m_kwh=energia_clip,

        energia_ac_anual_kwh=sum(energia_ac),
        energia_clipping_anual_kwh=sum(energia_clip),
    )
