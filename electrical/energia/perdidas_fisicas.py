from __future__ import annotations

"""
Aplicación de pérdidas físicas al sistema FV.
"""

from dataclasses import dataclass
from typing import List


Vector12 = List[float]


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class PerdidasResultado:

    ok: bool
    errores: List[str]

    energia_neta_12m_kwh: Vector12
    energia_neta_anual_kwh: float

    factor_perdidas_total: float


# ==========================================================
# API PUBLICA
# ==========================================================

def aplicar_perdidas(
    *,
    energia_dc_12m: Vector12,
    perdidas_dc_pct: float,
    perdidas_ac_pct: float,
    sombras_pct: float,
) -> PerdidasResultado:

    errores: List[str] = []

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if len(energia_dc_12m) != 12:
        errores.append("energia_dc_12m debe tener 12 valores.")

    if any(e is None for e in energia_dc_12m):
        errores.append("energia_dc_12m contiene valores None.")

    if any(e < 0 for e in energia_dc_12m if e is not None):
        errores.append("energia_dc_12m contiene valores negativos.")

    if not (0 <= perdidas_dc_pct <= 100):
        errores.append("perdidas_dc_pct fuera de rango.")

    if not (0 <= perdidas_ac_pct <= 100):
        errores.append("perdidas_ac_pct fuera de rango.")

    if not (0 <= sombras_pct <= 100):
        errores.append("sombras_pct fuera de rango.")

    energia: Vector12 = []
    f_total = 0.0

    # ------------------------------------------------------
    # FACTOR TOTAL DE PÉRDIDAS
    # ------------------------------------------------------

    if not errores:

        f_total = (
            (1.0 - perdidas_dc_pct / 100.0)
            * (1.0 - perdidas_ac_pct / 100.0)
            * (1.0 - sombras_pct / 100.0)
        )

        f_total = max(0.0, min(1.0, f_total))

        energia = [
            max(0.0, float(e) * f_total)
            for e in energia_dc_12m
        ]

    energia_anual = sum(energia)

    ok = len(errores) == 0

    return PerdidasResultado(
        ok=ok,
        errores=errores,
        energia_neta_12m_kwh=energia,
        energia_neta_anual_kwh=energia_anual,
        factor_perdidas_total=float(f_total),
    )
