from __future__ import annotations

"""
CÁLCULO DE GENERACIÓN DC BRUTA — FV Engine

Dominio: electrical.energia

Responsabilidad
---------------
Calcular la energía DC bruta generada por el sistema FV
antes de considerar pérdidas o limitaciones del inversor.

Modelo físico utilizado
-----------------------

E_mes = Pdc × HSP × días × factor_orientación

Donde:

    Pdc                potencia DC instalada (kW)
    HSP                horas solares pico del mes (kWh/m²/día)
    días               número de días del mes
    factor_orientación factor de ajuste por orientación e inclinación

La energía calculada corresponde a:

    generación DC bruta del sistema FV

Esta energía será posteriormente ajustada por:

    • pérdidas físicas
    • eficiencia del inversor
    • clipping DC/AC
"""

from dataclasses import dataclass
from typing import List

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
    Calcula la generación DC bruta del sistema FV.

    Parámetros
    ----------
    pdc_kw : float
        Potencia DC instalada del sistema.

    hsp_12m : List[float]
        Horas solares pico promedio para cada mes.

    dias_mes : List[int]
        Número de días de cada mes.

    factor_orientacion : float
        Factor de corrección por orientación e inclinación
        del generador FV.

    Retorna
    -------
    GeneracionBrutaResultado
        Energía DC mensual y anual generada por el sistema.
    """

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
    # CÁLCULO DE ENERGÍA MENSUAL
    # ------------------------------------------------------

    energia: Vector12 = []

    if not errores:

        for i in range(12):

            h = float(hsp_12m[i])
            d = int(dias_mes[i])

            # fórmula del modelo HSP
            e_mes = float(pdc_kw) * h * d * float(factor_orientacion)

            energia.append(e_mes)

    # ------------------------------------------------------
    # ENERGÍA ANUAL
    # ------------------------------------------------------

    energia_anual = sum(energia)

    ok = len(errores) == 0

    return GeneracionBrutaResultado(
        ok=ok,
        errores=errores,
        energia_mensual_dc_kwh=energia,
        energia_anual_dc_kwh=energia_anual,
    )
