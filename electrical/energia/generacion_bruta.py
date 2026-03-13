from __future__ import annotations

"""
Cálculo de generación DC bruta del sistema FV.

Modelo físico:

E_mes = Pdc × HSP × días × factor_orientación
"""

from dataclasses import dataclass
from typing import List

Vector12 = List[float]


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class GeneracionBrutaResultado:

    ok: bool
    errores: List[str]

    energia_mensual_dc_kwh: Vector12
    energia_anual_dc_kwh: float


# ==========================================================
# API PUBLICA
# ==========================================================

def calcular_energia_bruta_dc(
    *,
    pdc_kw: float,
    hsp_12m: Vector12,
    dias_mes: List[int],
    factor_orientacion: float,
) -> GeneracionBrutaResultado:

    errores: List[str] = []

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if pdc_kw <= 0:
        errores.append("pdc_kw inválido (<=0).")

    if len(hsp_12m) != 12:
        errores.append("hsp_12m debe tener 12 valores.")

    if len(dias_mes) != 12:
        errores.append("dias_mes debe tener 12 valores.")

    if factor_orientacion <= 0:
        errores.append("factor_orientacion inválido.")

    if any(h < 0 for h in hsp_12m):
        errores.append("hsp_12m contiene valores negativos.")

    if any(d <= 0 for d in dias_mes):
        errores.append("dias_mes contiene valores inválidos.")

    # ------------------------------------------------------
    # CÁLCULO DE ENERGÍA
    # ------------------------------------------------------

    energia: Vector12 = []

    if not errores:

        for i in range(12):

            h = float(hsp_12m[i])
            d = int(dias_mes[i])

            e_mes = float(pdc_kw) * h * d * float(factor_orientacion)

            energia.append(e_mes)

    energia_anual = sum(energia)

    ok = len(errores) == 0

    return GeneracionBrutaResultado(
        ok=ok,
        errores=errores,
        energia_mensual_dc_kwh=energia,
        energia_anual_dc_kwh=energia_anual,
    )
