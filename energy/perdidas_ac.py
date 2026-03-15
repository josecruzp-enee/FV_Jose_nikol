from __future__ import annotations

"""
APLICACIÓN DE PÉRDIDAS AC — FV Engine

Dominio: electrical.energia

Responsabilidad
---------------
Aplicar pérdidas eléctricas en el lado AC del sistema fotovoltaico.

Estas pérdidas ocurren después de la conversión del inversor y
representan efectos del sistema eléctrico:

    • cables AC
    • transformador (si existe)
    • tableros eléctricos
    • conexiones

Modelo utilizado
----------------

Las pérdidas se aplican mediante un factor multiplicativo:

    f_ac = (1 - perdidas_ac_pct)

La energía final entregada al sistema es:

    E_final = E_AC × f_ac

Este modelo es consistente con motores energéticos FV
utilizados en estimaciones de producción.
"""

from dataclasses import dataclass
from typing import List


Vector12 = List[float]


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class PerdidasACResultado:
    """
    Resultado de la aplicación de pérdidas AC.
    """

    ok: bool
    errores: List[str]

    energia_final_12m_kwh: Vector12
    # Energía AC final mensual después de pérdidas AC.

    energia_final_anual_kwh: float
    # Energía AC final anual.

    factor_perdidas_ac: float
    # Factor multiplicativo aplicado.


# ==========================================================
# API PUBLICA
# ==========================================================

def aplicar_perdidas_ac(
    *,
    energia_ac_12m: Vector12,
    perdidas_ac_pct: float,
) -> PerdidasACResultado:
    """
    Aplica pérdidas eléctricas en el lado AC.

    Parámetros
    ----------
    energia_ac_12m : List[float]
        Energía AC producida por el inversor (mensual).

    perdidas_ac_pct : float
        Porcentaje de pérdidas en el lado AC.

    Retorna
    -------
    PerdidasACResultado
        Energía final entregada al sistema.
    """

    errores: List[str] = []

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if len(energia_ac_12m) != 12:
        errores.append("energia_ac_12m debe tener 12 valores.")

    if any(e is None for e in energia_ac_12m):
        errores.append("energia_ac_12m contiene valores None.")

    if any(e < 0 for e in energia_ac_12m if e is not None):
        errores.append("energia_ac_12m contiene valores negativos.")

    if not (0 <= perdidas_ac_pct <= 100):
        errores.append("perdidas_ac_pct fuera de rango (0–100).")

    energia_final: Vector12 = []
    f_ac = 0.0

    # ------------------------------------------------------
    # CÁLCULO DEL FACTOR
    # ------------------------------------------------------

    if not errores:

        f_ac = 1.0 - (perdidas_ac_pct / 100.0)

        f_ac = max(0.0, min(1.0, f_ac))

        energia_final = [
            max(0.0, float(e) * f_ac)
            for e in energia_ac_12m
        ]

    # ------------------------------------------------------
    # ENERGÍA ANUAL
    # ------------------------------------------------------

    energia_anual = sum(energia_final)

    ok = len(errores) == 0

    return PerdidasACResultado(
        ok=ok,
        errores=errores,
        energia_final_12m_kwh=energia_final,
        energia_final_anual_kwh=energia_anual,
        factor_perdidas_ac=float(f_ac),
    )
