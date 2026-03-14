from __future__ import annotations

"""
MODELO ENERGÉTICO DEL INVERSOR — FV Engine

Dominio: electrical.energia

Modelo energético basado en:

• eficiencia variable del inversor
• clipping energético DC/AC
"""

from dataclasses import dataclass
from typing import List


Vector12 = List[float]


# ==========================================================
# ENTRADA
# ==========================================================

@dataclass
class EnergiaInversorInput:

    energia_dc_12m_kwh: Vector12

    # potencia DC instalada
    pdc_kw: float

    # potencia nominal AC
    kw_ac: float

    # eficiencia nominal
    eficiencia_nominal: float


# ==========================================================
# SALIDA
# ==========================================================

@dataclass
class EnergiaInversorResultado:

    energia_ac_12m_kwh: Vector12
    energia_clipping_12m_kwh: Vector12

    energia_ac_anual_kwh: float
    energia_clipping_anual_kwh: float


# ==========================================================
# MOTOR
# ==========================================================

def calcular_energia_inversor(
    inp: EnergiaInversorInput
) -> EnergiaInversorResultado:

    if len(inp.energia_dc_12m_kwh) != 12:
        raise ValueError("energia_dc_12m_kwh debe tener 12 valores")

    if inp.kw_ac <= 0:
        raise ValueError("kw_ac inválido")

    if not (0 < inp.eficiencia_nominal <= 1):
        raise ValueError("eficiencia_nominal inválida")

    # ------------------------------------------------------
    # carga relativa del inversor
    # ------------------------------------------------------

    carga_rel = min(1.5, inp.pdc_kw / inp.kw_ac)

    # ------------------------------------------------------
    # modelo de eficiencia variable
    # ------------------------------------------------------

    eficiencia_real = inp.eficiencia_nominal * (
        0.92 + 0.08 * min(1.0, carga_rel)
    )

    eficiencia_real = max(0.85, min(0.99, eficiencia_real))

    # ------------------------------------------------------
    # modelo de clipping energético
    # ------------------------------------------------------

    loss_clip = 0.0

    if carga_rel > 1:

        loss_clip = min(0.15, 0.5 * (carga_rel - 1) ** 2)

    energia_ac = []
    energia_clip = []

    # ------------------------------------------------------
    # cálculo mensual
    # ------------------------------------------------------

    for e_dc in inp.energia_dc_12m_kwh:

        e_ac = e_dc * eficiencia_real

        recorte = e_ac * loss_clip

        energia_clip.append(recorte)

        energia_ac.append(max(0.0, e_ac - recorte))

    return EnergiaInversorResultado(

        energia_ac_12m_kwh=energia_ac,
        energia_clipping_12m_kwh=energia_clip,

        energia_ac_anual_kwh=sum(energia_ac),
        energia_clipping_anual_kwh=sum(energia_clip),
    )
