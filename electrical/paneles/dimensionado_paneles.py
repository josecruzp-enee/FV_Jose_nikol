"""
DIMENSIONADO DE PANELES FV
==========================================================

Este módulo convierte una potencia DC objetivo en el
número de paneles necesarios y la potencia DC instalada.

NO calcula:
    - HSP
    - PR
    - consumo energético
    - strings
    - distribución MPPT

Solo determina:

    potencia DC objetivo → cantidad de paneles.

----------------------------------------------------------
ENTRADAS

Origen:
    electrical.paneles.entrada_panel.EntradaPaneles

Variables utilizadas:

    entrada.panel.pmax_w
        Potencia nominal del panel (W), dada por catálogos. 

    entrada.n_paneles_total
        Número total de paneles definido por el usuario. Esta si se hace de modo manual. 

    entrada.pdc_kw_objetivo
        Potencia DC objetivo del sistema (kW). Esta si se hace de modo automático para alcanzar una cobertura de demanda (80% predefinido).

----------------------------------------------------------
SALIDAS

Tipo retornado:
    PanelSizingResultado

Campos:

    ok
        Indica si el cálculo fue válido

    errores
        Lista de errores detectados

    kwp_req
        Potencia DC objetivo solicitada (kW)

    n_paneles
        Número final de paneles del sistema

    pdc_kw
        Potencia DC instalada del sistema (kW)

----------------------------------------------------------
CONSUMIDO POR

Archivo:
    electrical.paneles.orquestador_paneles

Flujo del dominio paneles:

    EntradaPaneles
        ↓
    dimensionar_paneles()
        ↓
    PanelSizingResultado
        ↓
    calculo_de_strings()

==========================================================
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
        return default


def _n_paneles(kwp_req: float, panel_w: float) -> int:

    if panel_w <= 0:
        raise ValueError("panel_w inválido (<=0).")

    if kwp_req <= 0:
        raise ValueError("pdc_kw_objetivo inválido (<=0).")

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

    # ------------------------------------------------------
    # POTENCIA DEL PANEL
    # ------------------------------------------------------

    try:
        panel_w = float(panel.pmax_w)
    except Exception:
        panel_w = 0.0
        errores.append("Panel inválido: pmax_w no numérica.")

    # ------------------------------------------------------
    # POTENCIA OBJETIVO
    # ------------------------------------------------------

    kwp_req = _safe_float(entrada.pdc_kw_objetivo, 0.0)

    # ------------------------------------------------------
    # VALIDAR CONFLICTO DE ENTRADAS
    # ------------------------------------------------------

    if entrada.n_paneles_total is not None and kwp_req > 0:

        errores.append(
            "Definir solo uno: n_paneles_total o pdc_kw_objetivo"
        )

    # ------------------------------------------------------
    # RESULTADOS
    # ------------------------------------------------------

    n_pan = 0
    pdc = 0.0

    if not errores:

        try:

            # --------------------------------------------------
            # CASO 1: usuario define número de paneles
            # --------------------------------------------------

            if entrada.n_paneles_total is not None:

                n_pan = int(entrada.n_paneles_total)

                if n_pan <= 0:
                    raise ValueError("n_paneles_total inválido")

            # --------------------------------------------------
            # CASO 2: usuario define potencia objetivo
            # --------------------------------------------------

            else:

                if kwp_req <= 0:
                    raise ValueError(
                        "pdc_kw_objetivo inválido o no definido."
                    )

                n_pan = _n_paneles(kwp_req, panel_w)

            # --------------------------------------------------
            # POTENCIA DC INSTALADA
            # --------------------------------------------------

            pdc = _pdc_kw(n_pan, panel_w)

        except Exception as e:

            errores.append(str(e))

    # ------------------------------------------------------
    # RESULTADO FINAL
    # ------------------------------------------------------

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
# Campos: ok : bool  ; errores : list[str]   ; kwp_req : float   ; n_paneles : int   ; pdc_kw : float; 
# Consumido por:
# electrical.paneles.orquestador_paneles
##########################################
# ==========================================================
