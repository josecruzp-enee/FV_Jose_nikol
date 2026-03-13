from __future__ import annotations

"""
Aplicación de pérdidas físicas al sistema FV.

Este módulo aplica pérdidas del sistema sobre la energía DC
generada por el generador fotovoltaico.

Incluye:
- pérdidas DC
- pérdidas AC
- sombras

NO aplica:
- clipping del inversor
- degradación anual
"""

from dataclasses import dataclass
from typing import List


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class PerdidasResultado:

    ok: bool
    errores: List[str]

    energia_neta_12m_kwh: List[float]

    factor_perdidas_total: float


# ==========================================================
# API PUBLICA
# ==========================================================

def aplicar_perdidas(
    *,
    energia_dc_12m: List[float],
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

    if any(e < 0 for e in energia_dc_12m):
        errores.append("energia_dc_12m contiene valores negativos.")

    if not (0 <= perdidas_dc_pct <= 100):
        errores.append("perdidas_dc_pct fuera de rango.")

    if not (0 <= perdidas_ac_pct <= 100):
        errores.append("perdidas_ac_pct fuera de rango.")

    if not (0 <= sombras_pct <= 100):
        errores.append("sombras_pct fuera de rango.")

    energia: List[float] = []
    f_total = 0.0

    # ------------------------------------------------------
    # CÁLCULO DE FACTOR TOTAL
    # ------------------------------------------------------

    if not errores:

        f_total = (
            (1.0 - perdidas_dc_pct / 100.0)
            * (1.0 - perdidas_ac_pct / 100.0)
            * (1.0 - sombras_pct / 100.0)
        )

        # asegurar rango físico
        f_total = max(0.0, min(1.0, f_total))

        energia = [max(0.0, float(e) * f_total) for e in energia_dc_12m]

    ok = len(errores) == 0

    return PerdidasResultado(
        ok=ok,
        errores=errores,
        energia_neta_12m_kwh=energia,
        factor_perdidas_total=float(f_total),
    )


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# PerdidasResultado
#
# Campos:
#
# ok : bool
# errores : list[str]
# energia_neta_12m_kwh : list[float]
# factor_perdidas_total : float
#
# Descripción:
# Energía mensual después de aplicar pérdidas del sistema FV.
#
# Consumido por:
# energia.limitacion_inversor
#
# ==========================================================
