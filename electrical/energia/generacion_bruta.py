# electrical/energia/generacion_bruta.py

"""
Cálculo de generación DC bruta del sistema FV.

Este módulo calcula la producción energética mensual del generador
fotovoltaico antes de aplicar pérdidas físicas o limitaciones de inversor.

Modelo físico:

E_mes = Pdc × HSP × días × factor_orientación

NO aplica:
- pérdidas
- clipping
- degradación
- limitación de inversor
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class GeneracionBrutaResultado:

    ok: bool
    errores: List[str]

    energia_mensual_dc_kwh: List[float]


# ==========================================================
# API PUBLICA
# ==========================================================

def calcular_energia_bruta_dc(
    *,
    pdc_kw: float,
    hsp_12m: List[float],
    dias_mes: List[int],
    factor_orientacion: float,
) -> GeneracionBrutaResultado:

    errores: List[str] = []

    if pdc_kw <= 0:
        errores.append("pdc_kw inválido (<=0).")

    if len(hsp_12m) != 12:
        errores.append("hsp_12m debe tener 12 valores.")

    if len(dias_mes) != 12:
        errores.append("dias_mes debe tener 12 valores.")

    if factor_orientacion <= 0:
        errores.append("factor_orientacion inválido.")

    energia: List[float] = []

    if not errores:

        energia = [
            float(pdc_kw) * float(h) * int(d) * float(factor_orientacion)
            for h, d in zip(hsp_12m, dias_mes)
        ]

    ok = len(errores) == 0

    return GeneracionBrutaResultado(
        ok=ok,
        errores=errores,
        energia_mensual_dc_kwh=energia,
    )


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# GeneracionBrutaResultado
#
# Campos:
#
# ok : bool
# errores : list[str]
# energia_mensual_dc_kwh : list[float]
#
# Descripción:
# Energía DC mensual producida por el generador FV antes de
# aplicar pérdidas o clipping.
#
# Consumido por:
# energia.perdidas_fisicas
#
# ==========================================================
