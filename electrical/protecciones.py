# electrical/protecciones.py
from __future__ import annotations

from electrical.modelos import ResultadoCorrientes, ResultadoProtecciones


def _redondear_breaker_standard(a: float) -> int:
    """
    Serie típica (simplificada). Luego lo pasas a catálogo real.
    """
    estandar = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 125, 150, 175, 200]
    for x in estandar:
        if x >= a:
            return x
    return estandar[-1]


def seleccionar_protecciones(corr: ResultadoCorrientes, cfg: dict) -> ResultadoProtecciones:
    """
    AC: breaker >= corriente de diseño
    DC: opcional (si luego modelas strings con fusibles por string)
    """
    breaker_ac = _redondear_breaker_standard(corr.i_ac_diseno_a)

    return ResultadoProtecciones(
        breaker_ac_a=int(breaker_ac),
        fusible_dc_a=None,
        disconnect_ac_a=int(breaker_ac),
        disconnect_dc_a=None,
    )
