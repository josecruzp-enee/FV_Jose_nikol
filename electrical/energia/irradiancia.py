# electrical/energia/irradiancia.py

from __future__ import annotations
from typing import List


DIAS_MES: List[int] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def hsp_honduras_conservador_12m() -> List[float]:
    """
    Modelo mensual conservador Honduras.
    Fuente simplificada para preview.
    """
    return [5.1, 5.4, 5.8, 5.6, 5.0, 4.5, 4.3, 4.4, 4.1, 4.0, 4.4, 4.7]
