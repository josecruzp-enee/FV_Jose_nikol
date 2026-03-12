from __future__ import annotations
from dataclasses import dataclass


# ==========================================================
# NIVEL DE CORRIENTE
# ==========================================================

@dataclass
class NivelCorriente:
    """
    Corriente en un nivel eléctrico del sistema FV.
    """

    i_operacion_a: float
    i_diseno_a: float


# ==========================================================
# RESULTADO DE CORRIENTES FV
# ==========================================================

@dataclass
class ResultadoCorrientes:
    """
    Corrientes del sistema FV separadas por nivel eléctrico.
    """

    panel: NivelCorriente
    string: NivelCorriente
    mppt: NivelCorriente
    dc_total: NivelCorriente
    ac: NivelCorriente
