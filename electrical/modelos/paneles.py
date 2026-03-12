from __future__ import annotations
from dataclasses import dataclass


"""
Modelos eléctricos del sistema FV.

FRONTERA DEL MÓDULO
===================

Entrada:
    Ninguna

Salida:
    PanelSpec
    ParametrosCableado

Consumido por:
    electrical.paneles
    electrical.inversor
    electrical.corrientes
    electrical.protecciones
    electrical.conductores
    electrical.nec

Este módulo define solo contratos de datos.
No contiene lógica ni cálculos.
"""


# ==========================================================
# ESPECIFICACIÓN DEL PANEL FV
# ==========================================================

@dataclass(frozen=True)
class PanelSpec:

    # potencia
    pmax_w: float

    # voltajes
    vmp_v: float
    voc_v: float

    # corrientes
    imp_a: float
    isc_a: float

    # coeficientes temperatura
    coef_voc_pct_c: float
    coef_vmp_pct_c: float


# ==========================================================
# PARÁMETROS DE CABLEADO
# ==========================================================

@dataclass(frozen=True)
class ParametrosCableado:

    # sistema AC
    vac: float = 240.0
    fases: int = 1
    fp: float = 1.0

    # distancias
    dist_dc_m: float = 15.0
    dist_ac_m: float = 25.0

    # caída de voltaje objetivo
    vdrop_obj_dc_pct: float = 2.0
    vdrop_obj_ac_pct: float = 2.0

    # configuración conductores
    incluye_neutro_ac: bool = False
    otros_ccc: int = 0

    # temperatura mínima ambiente
    t_min_c: float = 10.0
