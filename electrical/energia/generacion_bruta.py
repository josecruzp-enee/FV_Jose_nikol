from __future__ import annotations

"""
CÁLCULO DE GENERACIÓN DC BRUTA — FV Engine
==========================================

Dominio: electrical.energia

Responsabilidad
---------------
Calcular la energía DC bruta generada por el sistema
fotovoltaico antes de aplicar pérdidas del sistema
o limitaciones del inversor.

Modelo físico utilizado
-----------------------

    E_mes = Pdc × HSP × días × factor_orientación

Donde:

    Pdc                potencia DC instalada (kW)
    HSP                horas solares pico (kWh/m²/día)
    días               número de días del mes
    factor_orientación corrección por inclinación/orientación

La energía resultante corresponde a:

    generación DC bruta del sistema FV

Esta energía posteriormente será ajustada por:

    • pérdidas físicas
    • eficiencia del inversor
    • clipping DC/AC
"""

from dataclasses import dataclass
from typing import List


# ==========================================================
# TIPOS
# ==========================================================

Vector12 = List[float]


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class GeneracionBrutaResultado:
    """
    Resultado del cálculo de generación DC bruta.
    """

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
    """
    Calcula la generación DC bruta mensual y anual del sistema FV.

    Parámetros
    ----------
    pdc_kw : float
        Potencia DC instalada del generador FV (kW)

    hsp_12m : list[float]
        Horas solares pico promedio por mes (kWh/m²/día)

    dias_mes : list[int]
        Número de días de cada mes

    factor_orientacion : float
        Factor de corrección por orientación/inclinación

    Retorna
    -------
    GeneracionBrutaResultado
    """

    errores: List[str] = []

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if pdc_kw <= 0:
        errores.append("pdc_kw inválido (<=0)")

    if len(hsp_12m) != 12:
        errores.append("hsp_12m debe contener 12 valores")

    if len(dias_mes) != 12:
        errores.append("dias_mes debe contener 12 valores")

    if factor_orientacion <= 0:
        errores.append("factor_orientacion inválido")

    if any(h < 0 for h in hsp_12m):
        errores.append("hsp_12m contiene valores negativos")

    if any(d <= 0 for d in dias_mes):
        errores.append("dias_mes contiene valores inválidos")

    # Si hay errores se retorna estructura consistente
    if errores:
        return GeneracionBrutaResultado(
            ok=False,
            errores=errores,
            energia_mensual_dc_kwh=[0.0] * 12,
            energia_anual_dc_kwh=0.0,
        )

    # ------------------------------------------------------
    # CÁLCULO DE ENERGÍA MENSUAL
    # ------------------------------------------------------

    energia: Vector12 = []

    for i in range(12):

        hsp_mes = float(hsp_12m[i])
        dias = int(dias_mes[i])

        # Modelo HSP
        e_mes = pdc_kw * hsp_mes * dias * factor_orientacion

        energia.append(e_mes)

    # ------------------------------------------------------
    # ENERGÍA ANUAL
    # ------------------------------------------------------

    energia_anual = sum(energia)

    # ------------------------------------------------------
    # RESULTADO
    # ------------------------------------------------------

    return GeneracionBrutaResultado(
        ok=True,
        errores=[],
        energia_mensual_dc_kwh=energia,
        energia_anual_dc_kwh=energia_anual,
    )
