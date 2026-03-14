from __future__ import annotations

"""
MODELO ENERGÉTICO DEL INVERSOR — FV Engine

Dominio: electrical.energia

Responsabilidad
---------------
Calcular la producción energética AC del sistema FV considerando:

• eficiencia del inversor
• eficiencia parcial por carga
• pérdidas por clipping DC/AC

Este modelo opera a nivel energético mensual.
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
    Parámetros energéticos del sistema FV.
    """

    energia_dc_12m_kwh: Vector12

    # potencia DC instalada
    pdc_kw: float

    # potencia nominal AC del inversor
    kw_ac: float

    # eficiencia nominal del inversor (0–1)
    eficiencia_nominal: float


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
# MOTOR DEL INVERSOR
# ==========================================================

def calcular_energia_inversor(inp: EnergiaInversorInput) -> EnergiaInversorResultado:
    """
    Calcula la producción energética AC del inversor
    considerando eficiencia y clipping energético.
    """

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if len(inp.energia_dc_12m_kwh) != 12:
        raise ValueError("energia_dc_12m_kwh debe tener 12 valores")

    if inp.kw_ac <= 0:
        raise ValueError("kw_ac inválido")

    if not (0 < inp.eficiencia_nominal <= 1):
        raise ValueError("eficiencia_nominal fuera de rango")

    # ------------------------------------------------------
    # DC/AC ratio
    # ------------------------------------------------------

    ratio = inp.pdc_kw / inp.kw_ac

    # ------------------------------------------------------
    # modelo simplificado de eficiencia parcial
    # ------------------------------------------------------

    # inversores son menos eficientes con baja carga
    carga_relativa = min(1.0, ratio)

    eficiencia_real = inp.eficiencia_nominal * (
        0.9 + 0.1 * carga_relativa
    )

    # ------------------------------------------------------
    # modelo de clipping energético
    # ------------------------------------------------------

    loss_clip = 0.0

    if ratio > 1:
        loss_clip = min(0.15, 0.5 * (ratio - 1) ** 2)

    energia_ac: Vector12 = []
    energia_clip: Vector12 = []

    # ------------------------------------------------------
    # cálculo mensual
    # ------------------------------------------------------

    for e_dc in inp.energia_dc_12m_kwh:

        if e_dc < 0:
            raise ValueError("energía DC negativa")

        # conversión DC → AC
        e_ac = e_dc * eficiencia_real

        # pérdidas por clipping
        recorte = e_ac * loss_clip

        energia_clip.append(recorte)

        energia_ac.append(max(0.0, e_ac - recorte))

    # ------------------------------------------------------
    # resultado
    # ------------------------------------------------------

    return EnergiaInversorResultado(

        energia_ac_12m_kwh=energia_ac,
        energia_clipping_12m_kwh=energia_clip,

        energia_ac_anual_kwh=sum(energia_ac),
        energia_clipping_anual_kwh=sum(energia_clip),
    )
