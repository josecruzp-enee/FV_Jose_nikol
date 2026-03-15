from __future__ import annotations

"""
APLICACIÓN DE PÉRDIDAS FÍSICAS — FV Engine

Dominio: electrical.energia

Responsabilidad
---------------
Aplicar pérdidas físicas al sistema fotovoltaico después de
calcular la generación DC bruta.

Estas pérdidas representan efectos reales del sistema:

    • pérdidas DC (cables, mismatch, suciedad)
    • pérdidas AC (eficiencia inversor, cables AC)
    • pérdidas por sombras

Modelo utilizado
----------------

Las pérdidas se aplican mediante un factor multiplicativo total:

    f_total =
        (1 - pérdidas_DC)
      × (1 - pérdidas_AC)
      × (1 - sombras)

La energía neta resultante es:

    E_neta = E_DC × f_total

Este modelo es ampliamente utilizado en estimaciones
energéticas de sistemas FV.
"""

from dataclasses import dataclass
from typing import List


Vector12 = List[float]


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class PerdidasResultado:
    """
    Resultado del cálculo de pérdidas físicas.
    """

    ok: bool
    errores: List[str]

    # energía mensual después de pérdidas
    energia_neta_12m_kwh: Vector12

    # energía anual después de pérdidas
    energia_neta_anual_kwh: float

    # factor total aplicado
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
    """
    Aplica pérdidas físicas al sistema FV.

    Parámetros
    ----------
    energia_dc_12m : List[float]
        Energía DC bruta mensual generada por el sistema.

    perdidas_dc_pct : float
        Porcentaje de pérdidas en el lado DC.

    perdidas_ac_pct : float
        Porcentaje de pérdidas en el lado AC.

    sombras_pct : float
        Porcentaje de pérdidas por sombreado.

    Retorna
    -------
    PerdidasResultado
        Energía neta mensual y anual después de pérdidas.
    """

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
        errores.append("perdidas_dc_pct fuera de rango (0–100).")

    if not (0 <= perdidas_ac_pct <= 100):
        errores.append("perdidas_ac_pct fuera de rango (0–100).")

    if not (0 <= sombras_pct <= 100):
        errores.append("sombras_pct fuera de rango (0–100).")

    energia: Vector12 = []
    f_total = 0.0

    # ------------------------------------------------------
    # FACTOR TOTAL DE PÉRDIDAS
    # ------------------------------------------------------

    if not errores:

        # conversión a factores multiplicativos
        f_total = (
            (1.0 - perdidas_dc_pct / 100.0)
            * (1.0 - sombras_pct / 100.0)
        )

        # seguridad numérica
        f_total = max(0.0, min(1.0, f_total))

        # --------------------------------------------------
        # APLICACIÓN A ENERGÍA MENSUAL
        # --------------------------------------------------

        energia = [
            max(0.0, float(e) * f_total)
            for e in energia_dc_12m
        ]

    # ------------------------------------------------------
    # ENERGÍA ANUAL
    # ------------------------------------------------------

    energia_anual = sum(energia)

    ok = len(errores) == 0

    return PerdidasResultado(
        ok=ok,
        errores=errores,
        energia_neta_12m_kwh=energia,
        energia_neta_anual_kwh=energia_anual,
        factor_perdidas_total=float(f_total),
    )
