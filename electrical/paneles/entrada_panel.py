from __future__ import annotations

"""
CONTRATO DE ENTRADA — DOMINIO PANELES

Este archivo define la estructura de datos que recibe el
dominio de paneles para calcular la configuración del
generador fotovoltaico.

Este módulo NO contiene lógica de cálculo.

Responsabilidad:
    Definir la estructura tipada de entrada para el
    orquestador del dominio paneles.

Consumido por:
    electrical.paneles.orquestador_paneles
"""

from dataclasses import dataclass
from typing import Optional

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


# ==========================================================
# ENTRADA DEL DOMINIO PANELES
# ==========================================================

@dataclass
class EntradaPaneles:
    """
    Parámetros de entrada requeridos para calcular
    la configuración de strings del generador FV.
    """

    # ----------------------------------------------
    # Equipos
    # ----------------------------------------------

    panel: PanelSpec
    inversor: InversorSpec

    # ----------------------------------------------
    # Sistema FV
    # ----------------------------------------------

    n_paneles_total: int
    n_inversores: Optional[int] = None
    # ----------------------------------------------
    # Condiciones térmicas
    # ----------------------------------------------

    t_min_c: float
    t_oper_c: float

    # ----------------------------------------------
    # Configuración de instalación
    # ----------------------------------------------

    dos_aguas: bool = False

    # ----------------------------------------------
    # Objetivo de diseño
    # ----------------------------------------------

    objetivo_dc_ac: Optional[float] = None

    pdc_kw_objetivo: Optional[float] = None


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# EntradaPaneles
#
# Campos:
#
# panel : PanelSpec
# inversor : InversorSpec
#
# n_paneles_total : int
#
# t_min_c : float
# t_oper_c : float
#
# dos_aguas : bool
#
# objetivo_dc_ac : Optional[float]
# pdc_kw_objetivo : Optional[float]
#
# Consumido por:
# electrical.paneles.orquestador_paneles
#
# ==========================================================
