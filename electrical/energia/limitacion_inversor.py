# electrical/energia/limitacion_inversor.py
from typing import List


def aplicar_curtailment(
    *,
    energia_12m: List[float],
    pdc_kw: float,
    pac_kw: float,
    permitir: bool,
) -> (List[float], List[float]):

    if not permitir or pac_kw <= 0:
        return energia_12m, [0.0] * 12

    ratio = pdc_kw / pac_kw

    if ratio <= 1.0:
        return energia_12m, [0.0] * 12

    # Modelo simple: exceso proporcional
    exceso_factor = min(1.0, (ratio - 1.0) * 0.5)

    energia_recortada = [e * exceso_factor for e in energia_12m]
    energia_final = [e - r for e, r in zip(energia_12m, energia_recortada)]

    return energia_final, energia_recortada
