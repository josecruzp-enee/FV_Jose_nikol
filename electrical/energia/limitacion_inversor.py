from __future__ import annotations

"""
MODELO ELÉCTRICO DEL INVERSOR — FV Engine

Dominio: electrical.energia.inversor

Responsabilidad
---------------
Simular el comportamiento eléctrico instantáneo del inversor
fotovoltaico durante la conversión DC → AC.

Este modelo representa el límite físico del inversor cuando
la potencia DC del generador supera la capacidad AC del equipo.

Conceptos físicos modelados
---------------------------

1) Conversión DC → AC

    P_AC = P_DC × eficiencia

2) Límite de potencia del inversor

    Cuando:

        P_AC_teórica > P_AC_nominal

    el inversor limita su salida a su potencia nominal.

    Esto se conoce como:

        CLIPPING

3) Energía recortada

    Es la potencia que el inversor no puede entregar
    debido a su límite AC.

Relación en el motor FV
-----------------------

    potencia_arreglo
            ↓
    modelo_inversor   ← ESTE MÓDULO
            ↓
    modelo energético del inversor
            ↓
    producción energética final
"""

from dataclasses import dataclass


# ==========================================================
# ENTRADA DEL MODELO
# ==========================================================

@dataclass
class InversorInput:
    """
    Parámetros eléctricos de entrada del inversor.
    """

    # Potencia DC entregada por el generador FV
    pdc_w: float

    # Potencia nominal AC del inversor
    kw_ac_nominal: float

    # Eficiencia nominal del inversor (0–1)
    eficiencia_nominal: float


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass
class InversorResultado:
    """
    Resultado del modelo eléctrico del inversor.
    """

    # potencia AC entregada por el inversor
    pac_w: float

    # eficiencia aplicada
    eficiencia: float

    # potencia recortada por clipping
    clipping_w: float


# ==========================================================
# MOTOR DEL INVERSOR
# ==========================================================

def calcular_operacion_inversor(inp: InversorInput) -> InversorResultado:
    """
    Calcula la potencia AC entregada por el inversor
    a partir de la potencia DC del generador.

    Parámetros
    ----------
    inp : InversorInput
        Condiciones eléctricas del inversor.

    Retorna
    -------
    InversorResultado
        Estado eléctrico del inversor.
    """

    # ------------------------------------------------------
    # Validación básica
    # ------------------------------------------------------

    if inp.pdc_w < 0:
        raise ValueError("pdc_w inválido")

    # potencia máxima AC del inversor
    pac_max = inp.kw_ac_nominal * 1000

    # ------------------------------------------------------
    # Conversión DC → AC
    # ------------------------------------------------------

    pac_teorica = inp.pdc_w * inp.eficiencia_nominal

    # ------------------------------------------------------
    # Verificación de clipping
    # ------------------------------------------------------

    if pac_teorica <= pac_max:

        pac = pac_teorica
        clipping = 0.0

    else:

        pac = pac_max
        clipping = pac_teorica - pac_max

    # ------------------------------------------------------
    # Resultado
    # ------------------------------------------------------

    return InversorResultado(

        pac_w=pac,
        eficiencia=inp.eficiencia_nominal,
        clipping_w=clipping,
    )
