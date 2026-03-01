# electrical/energia/generacion_bruta.py
from typing import List


def calcular_energia_bruta_dc(
    *,
    pdc_kw: float,
    hsp_12m: List[float],
    dias_mes: List[int],
    factor_orientacion: float,
) -> List[float]:
    """
    Energía DC bruta mensual sin pérdidas ni clipping.
    """
    return [
        pdc_kw * h * d * factor_orientacion
        for h, d in zip(hsp_12m, dias_mes)
    ]
