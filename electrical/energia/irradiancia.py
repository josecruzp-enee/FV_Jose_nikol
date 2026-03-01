# electrical/energia/irradiancia.py

from __future__ import annotations
from typing import List


DIAS_MES: List[int] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def hsp_12m_base() -> List[float]:
    """
    Perfil mensual oficial HSP – Honduras.
    Único origen válido del sistema.
    """

    return [
        5.1,  # Ene
        5.4,  # Feb
        5.8,  # Mar
        5.6,  # Abr
        5.0,  # May
        4.5,  # Jun
        4.3,  # Jul
        4.4,  # Ago
        4.1,  # Sep
        4.0,  # Oct
        4.4,  # Nov
        4.7,  # Dic
    ]
