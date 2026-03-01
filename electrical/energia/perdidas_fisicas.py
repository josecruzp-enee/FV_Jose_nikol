# electrical/energia/perdidas_fisicas.py
from typing import List


def aplicar_perdidas(
    *,
    energia_dc_12m: List[float],
    perdidas_dc_pct: float,
    perdidas_ac_pct: float,
    sombras_pct: float,
) -> List[float]:

    f_total = (
        (1.0 - perdidas_dc_pct / 100.0)
        * (1.0 - perdidas_ac_pct / 100.0)
        * (1.0 - sombras_pct / 100.0)
    )

    f_total = max(0.0, min(1.0, f_total))

    return [e * f_total for e in energia_dc_12m]
