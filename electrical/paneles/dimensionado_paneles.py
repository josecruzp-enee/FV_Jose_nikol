from __future__ import annotations

"""
DIMENSIONADO DE PANELES — FV ENGINE

Convierte una potencia DC objetivo o una cantidad de paneles
en un sistema FV definido en potencia instalada.

NO calcula:
    - energía
    - strings
    - MPPT
    - pérdidas

Solo resuelve:

    tamaño del sistema (paneles y potencia DC)
"""

from dataclasses import dataclass
from math import ceil
from typing import List

from electrical.paneles.entrada_panel import EntradaPaneles


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class PanelSizingResultado:

    ok: bool
    errores: List[str]

    kwp_req: float
    n_paneles: int
    pdc_kw: float


# ==========================================================
# UTILIDADES
# ==========================================================

def _calcular_n_paneles(kwp_req: float, panel_w: float) -> int:

    if panel_w <= 0:
        raise ValueError("panel_w inválido (<=0).")

    if kwp_req <= 0:
        raise ValueError("pdc_kw_objetivo inválido (<=0).")

    return max(1, int(ceil((kwp_req * 1000.0) / panel_w)))


def _calcular_pdc_kw(n_paneles: int, panel_w: float) -> float:

    if n_paneles <= 0:
        raise ValueError("n_paneles inválido (<=0).")

    if panel_w <= 0:
        raise ValueError("panel_w inválido (<=0).")

    return (n_paneles * panel_w) / 1000.0


# ==========================================================
# API PUBLICA
# ==========================================================

def dimensionar_paneles(
    entrada: EntradaPaneles,
) -> PanelSizingResultado:

    errores: List[str] = []

    # ------------------------------------------------------
    # VALIDACIÓN PANEL
    # ------------------------------------------------------

    try:
        panel_w = float(entrada.panel.pmax_w)
    except Exception:
        return PanelSizingResultado(
            ok=False,
            errores=["Panel inválido: pmax_w no numérica"],
            kwp_req=0.0,
            n_paneles=0,
            pdc_kw=0.0,
        )

    # ------------------------------------------------------
    # VALIDACIÓN ENTRADAS
    # ------------------------------------------------------

    if (
        entrada.n_paneles_total is not None
        and entrada.pdc_kw_objetivo is not None
    ):
        return PanelSizingResultado(
            ok=False,
            errores=["Definir solo uno: n_paneles_total o pdc_kw_objetivo"],
            kwp_req=0.0,
            n_paneles=0,
            pdc_kw=0.0,
        )

    # ------------------------------------------------------
    # CASOS DE DIMENSIONAMIENTO
    # ------------------------------------------------------

    try:

        # CASO 1 → manual
        if entrada.n_paneles_total is not None:

            n_paneles = int(entrada.n_paneles_total)

            if n_paneles <= 0:
                raise ValueError("n_paneles_total inválido")

            kwp_req = (n_paneles * panel_w) / 1000.0

        # CASO 2 → automático
        else:

            kwp_req = float(entrada.pdc_kw_objetivo or 0.0)

            if kwp_req <= 0:
                raise ValueError(
                    "pdc_kw_objetivo no definido o inválido"
                )

            n_paneles = _calcular_n_paneles(kwp_req, panel_w)

        # --------------------------------------------------
        # POTENCIA FINAL
        # --------------------------------------------------

        pdc_kw = _calcular_pdc_kw(n_paneles, panel_w)

        return PanelSizingResultado(
            ok=True,
            errores=[],
            kwp_req=float(kwp_req),
            n_paneles=int(n_paneles),
            pdc_kw=float(pdc_kw),
        )

    except Exception as e:

        return PanelSizingResultado(
            ok=False,
            errores=[str(e)],
            kwp_req=0.0,
            n_paneles=0,
            pdc_kw=0.0,
        )


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# dimensionar_paneles()
#
# Entrada:
#   EntradaPaneles
#       - panel (pmax_w)
#       - n_paneles_total (opcional)
#       - pdc_kw_objetivo (opcional)
#
# Proceso:
#   - valida coherencia de entradas
#   - calcula número de paneles o usa valor directo
#   - calcula potencia DC instalada
#
# Salida:
#   PanelSizingResultado
#
# Campos:
#   ok            → estado del cálculo
#   errores       → lista de errores
#   kwp_req       → potencia objetivo
#   n_paneles     → número final de paneles
#   pdc_kw        → potencia instalada
#
# Consumido por:
#   electrical.paneles.orquestador_paneles
#
# Ubicación en flujo:
#
#   EntradaPaneles
#       ↓
#   dimensionar_paneles
#       ↓
#   calculo_de_strings
#
# ==========================================================
