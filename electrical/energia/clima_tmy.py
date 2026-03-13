from __future__ import annotations

"""
MODELO CLIMÁTICO — FV Engine

Responsabilidad
---------------
Proveer datos climáticos horarios para el motor 8760.

Datos entregados:

• GHI (irradiancia global horizontal)
• temperatura ambiente

Estos datos alimentan:

solar
paneles
simulación energética
"""

from dataclasses import dataclass
from typing import List


# ==========================================================
# ESTRUCTURA DE DATOS CLIMÁTICOS
# ==========================================================

@dataclass
class ClimaHora:

    ghi_wm2: float
    temp_amb_c: float


# ==========================================================
# GENERADOR SIMPLE DE CLIMA (placeholder)
# ==========================================================

def generar_clima_base() -> List[ClimaHora]:
    """
    Genera un clima simplificado de 8760 horas.
    Este es solo un placeholder hasta integrar
    TMY o PVGIS.
    """

    clima = []

    for h in range(8760):

        # irradiancia simplificada
        hora_dia = h % 24

        if 6 <= hora_dia <= 18:
            ghi = 800
        else:
            ghi = 0

        temp = 30

        clima.append(
            ClimaHora(
                ghi_wm2=ghi,
                temp_amb_c=temp
            )
        )

    return clima
