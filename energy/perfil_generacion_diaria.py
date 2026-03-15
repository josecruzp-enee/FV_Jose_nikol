from __future__ import annotations

"""
PERFIL HORARIO DE GENERACIÓN FV

Genera una curva típica diaria de producción fotovoltaica
para 24 horas.

No usa clima real.
Solo genera un perfil solar ideal para visualización.
"""

from typing import List
import math


# ==========================================================
# PERFIL FV
# ==========================================================

def perfil_generacion_diaria(
    pdc_kw: float,
    eficiencia_inversor: float = 0.96
) -> List[float]:
    """
    Genera perfil de potencia FV horario (24 horas).

    Parámetros
    ----------
    pdc_kw : float
        Potencia DC instalada

    eficiencia_inversor : float
        eficiencia DC → AC

    Retorna
    -------
    List[float]
        Potencia FV por hora (kW)
    """

    potencia_horaria = []

    for hora in range(24):

        # perfil solar tipo seno
        angulo = (hora - 6) / 12 * math.pi

        if 6 <= hora <= 18:

            irradiancia_relativa = math.sin(angulo)

            potencia = (
                pdc_kw
                * irradiancia_relativa
                * eficiencia_inversor
            )

            potencia = max(potencia, 0)

        else:

            potencia = 0

        potencia_horaria.append(round(potencia, 2))

    return potencia_horaria
