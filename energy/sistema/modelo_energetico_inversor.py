from __future__ import annotations

"""
MODELO ENERGÉTICO DEL INVERSOR — FV Engine

Dominio: electrical.energia

Responsabilidad
---------------
Modelar la conversión energética DC → AC del inversor considerando:

    • eficiencia dependiente de carga
    • clipping energético DC/AC

Este modelo trabaja a nivel energético mensual (no horario).

Modelo utilizado
----------------

1) Eficiencia dependiente de carga

    η_real = η_nominal × (0.95 + 0.05 × carga_rel)

donde:

    carga_rel = min(1 , DC/AC)

2) Clipping energético aproximado

    clipping ≈ 0.04 × (DC/AC − 1)²

limitado a un máximo de 15%.

Este modelo reproduce de forma razonable el comportamiento
energético de inversores en simulaciones simplificadas.
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
    # Energía DC mensual disponible a la entrada del inversor.

    pdc_kw: float
    # Potencia DC instalada del generador FV.

    kw_ac: float
    # Potencia nominal AC del inversor.

    eficiencia_nominal: float
    # Eficiencia nominal del inversor (0–1).


# ==========================================================
# SALIDA
# ==========================================================

@dataclass
class EnergiaInversorResultado:

    energia_ac_12m_kwh: Vector12
    # Energía AC producida por el inversor (mensual).

    energia_clipping_12m_kwh: Vector12
    # Energía perdida por clipping (mensual).

    energia_ac_anual_kwh: float
    # Energía AC anual.

    energia_clipping_anual_kwh: float
    # Energía anual perdida por clipping.


# ==========================================================
# MOTOR
# ==========================================================

def calcular_energia_inversor(
    inp: EnergiaInversorInput
) -> EnergiaInversorResultado:

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if len(inp.energia_dc_12m_kwh) != 12:
        raise ValueError("energia_dc_12m_kwh debe tener 12 valores")

    if inp.kw_ac <= 0:
        raise ValueError("kw_ac inválido")

    if inp.pdc_kw <= 0:
        raise ValueError("pdc_kw inválido")

    if not (0 < inp.eficiencia_nominal <= 1):
        raise ValueError("eficiencia_nominal inválida")


    # ------------------------------------------------------
    # RELACIÓN DC / AC
    # ------------------------------------------------------

    dc_ac_ratio = inp.pdc_kw / inp.kw_ac


    # ------------------------------------------------------
    # EFICIENCIA DEPENDIENTE DE CARGA
    # ------------------------------------------------------

    carga_rel = min(1.0, dc_ac_ratio)

    eficiencia_real = inp.eficiencia_nominal * (
        0.95 + 0.05 * carga_rel
    )

    eficiencia_real = max(0.90, min(0.99, eficiencia_real))


    # ------------------------------------------------------
    # MODELO DE CLIPPING ENERGÉTICO
    # ------------------------------------------------------

    loss_clip = 0.0

    if dc_ac_ratio > 1:

        loss_clip = 0.04 * (dc_ac_ratio - 1) ** 2

        loss_clip = min(0.15, loss_clip)


    energia_ac: Vector12 = []
    energia_clip: Vector12 = []


    # ------------------------------------------------------
    # CÁLCULO MENSUAL
    # ------------------------------------------------------

    for e_dc in inp.energia_dc_12m_kwh:

        e_dc = float(e_dc)

        # conversión DC → AC
        e_ac = e_dc * eficiencia_real

        # clipping
        recorte = e_ac * loss_clip

        energia_clip.append(recorte)

        energia_ac.append(max(0.0, e_ac - recorte))


    # ------------------------------------------------------
    # ENERGÍA ANUAL
    # ------------------------------------------------------

    energia_ac_anual = sum(energia_ac)
    energia_clip_anual = sum(energia_clip)


    return EnergiaInversorResultado(

        energia_ac_12m_kwh=energia_ac,
        energia_clipping_12m_kwh=energia_clip,

        energia_ac_anual_kwh=energia_ac_anual,
        energia_clipping_anual_kwh=energia_clip_anual,
    )


def calcular_inversor_8760(
    potencia_dc_kw_8760: list[float],
    p_ac_nominal_kw: float,
    eficiencia_nominal: float = 0.97
):
    """
    Modelo horario del inversor FV (8760).
    """

    if p_ac_nominal_kw <= 0:
        raise ValueError("p_ac_nominal_kw inválido")

    if not (0 < eficiencia_nominal <= 1):
        raise ValueError("eficiencia_nominal inválida")

    potencia_ac_kw = []
    clipping_kw = []

    for p_dc in potencia_dc_kw_8760:

        p_ac = p_dc * eficiencia_nominal

        if p_ac > p_ac_nominal_kw:

            clip = p_ac - p_ac_nominal_kw
            p_ac = p_ac_nominal_kw

        else:

            clip = 0.0

        potencia_ac_kw.append(p_ac)
        clipping_kw.append(clip)

    energia_ac_anual = sum(potencia_ac_kw)
    energia_clipping_anual = sum(clipping_kw)

    return {

        "potencia_ac_kw_8760": potencia_ac_kw,
        "clipping_kw_8760": clipping_kw,

        "energia_ac_anual_kwh": energia_ac_anual,
        "energia_clipping_anual_kwh": energia_clipping_anual,

        "horas": len(potencia_ac_kw)
    }
