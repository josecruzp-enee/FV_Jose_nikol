"""
CLIPPING DEL INVERSOR — FV Engine

Dominio: electrical.inversor

Responsabilidad
---------------
Calcular la potencia AC entregada por el inversor cuando la
potencia DC del campo FV supera la capacidad del inversor.

Este módulo modela el fenómeno de clipping.

Modelo
------
potencia_ac_potencial = potencia_dc * eficiencia

potencia_ac = min(potencia_ac_potencial, potencia_ac_nominal)

clipping = max(0, potencia_ac_potencial - potencia_ac_nominal)
"""

from dataclasses import dataclass


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass
class ClippingInput:
    """
    Entrada del modelo de clipping
    """

    potencia_dc: float
    potencia_ac_nominal: float
    eficiencia: float


@dataclass
class ClippingResultado:
    """
    Resultado del cálculo
    """

    potencia_ac: float
    clipping: float


# ==========================================================
# MOTOR DE CLIPPING
# ==========================================================

def calcular_clipping(inp: ClippingInput) -> ClippingResultado:

    pdc = inp.potencia_dc
    pac_nom = inp.potencia_ac_nominal
    eff = inp.eficiencia

    # potencia AC potencial
    pac_potencial = pdc * eff

    # potencia real del inversor
    potencia_ac = min(pac_potencial, pac_nom)

    # potencia perdida por clipping
    clipping = max(0.0, pac_potencial - pac_nom)

    return ClippingResultado(
        potencia_ac=potencia_ac,
        clipping=clipping
    )
