"""
Dimensionado de paneles FV.

Convierte potencia DC objetivo en número de paneles y potencia DC instalada.
Este módulo NO calcula HSP, PR ni consumo energético.
"""

from __future__ import annotations

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

def _safe_float(x, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _n_paneles(kwp_req: float, panel_w: float) -> int:

    if panel_w <= 0:
        raise ValueError("panel_w inválido (<=0).")

    if kwp_req <= 0:
        raise ValueError("kwp_req inválido (<=0).")

    return max(1, int(ceil((kwp_req * 1000.0) / panel_w)))


def _pdc_kw(n_paneles: int, panel_w: float) -> float:

    return (int(n_paneles) * float(panel_w)) / 1000.0


# ==========================================================
# API PUBLICA
# ==========================================================

def dimensionar_paneles(
    entrada: EntradaPaneles,
) -> PanelSizingResultado:

    errores: List[str] = []

    panel = entrada.panel

    try:
        panel_w = float(panel.potencia_w)
    except Exception:
        panel_w = 0.0
        errores.append("Panel inválido: potencia_w no numérica.")

    kwp_req = _safe_float(entrada.pdc_kw_objetivo, 0.0)

    n_pan = 0
    pdc = 0.0

    if not errores:

        try:

            if entrada.n_paneles_total is not None:

                n_pan = int(entrada.n_paneles_total)

            else:

                if kwp_req <= 0:
                    raise ValueError("pdc_kw_objetivo inválido o no definido.")

                n_pan = _n_paneles(kwp_req, panel_w)

            pdc = _pdc_kw(n_pan, panel_w)

        except Exception as e:

            errores.append(str(e))

    ok = len(errores) == 0

    return PanelSizingResultado(
        ok=ok,
        errores=errores,
        kwp_req=float(kwp_req),
        n_paneles=int(n_pan),
        pdc_kw=float(pdc),
    )


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# PanelSizingResultado
#
# Campos:
#
# ok : bool
# errores : list[str]
# kwp_req : float
# n_paneles : int
# pdc_kw : float
#
# Consumido por:
# electrical.paneles.calculo_de_strings
#
# ==========================================================
