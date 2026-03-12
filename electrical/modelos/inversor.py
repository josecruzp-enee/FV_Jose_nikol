# electrical/catalogos/modelos.py
from __future__ import annotations
from dataclasses import dataclass

"""
Modelos de equipos del dominio eléctrico FV.

FRONTERA DEL MÓDULO
===================

Entrada:
    Ninguna

Salida:
    InversorSpec
    ParametrosCableado

Consumido por:
    electrical.paneles
    electrical.inversor
    electrical.corrientes
    electrical.protecciones
    electrical.conductores
    electrical.nec
    core.servicios

Este módulo define únicamente CONTRATOS DE DATOS.
No contiene lógica ni cálculos.
"""


# ==========================================================
# ESPECIFICACIÓN DE INVERSOR FV
# ==========================================================

@dataclass(frozen=True)
class InversorSpec:
    """
    Especificación eléctrica mínima de un inversor FV.
    """

    # potencia AC nominal del inversor
    kw_ac: float

    # número de MPPT
    n_mppt: int

    # ventana MPPT
    mppt_min_v: float
    mppt_max_v: float

    # voltaje máximo DC permitido
    vdc_max_v: float

    # corriente máxima por MPPT (datasheet)
    imppt_max_a: float | None = None


# ==========================================================
# PARÁMETROS GENERALES DE CABLEADO
# ==========================================================

@dataclass(frozen=True)
class ParametrosCableado:
    """
    Parámetros globales usados por el motor de ingeniería eléctrica.
    """

    # sistema AC
    vac: float = 240.0
    fases: int = 1
    fp: float = 1.0

    # distancias estimadas
    dist_dc_m: float = 15.0
    dist_ac_m: float = 25.0

    # caída de voltaje objetivo
    vdrop_obj_dc_pct: float = 2.0
    vdrop_obj_ac_pct: float = 2.0

    # configuración de conductores
    incluye_neutro_ac: bool = False
    otros_ccc: int = 0

    # temperatura mínima ambiente (para cálculo Voc frío)
    t_min_c: float = 10.0


# ==========================================================
# SALIDAS DEL MÓDULO
# ==========================================================
#
# Exporta:
#
#   InversorSpec
#   ParametrosCableado
#
# Usado por:
#
#   electrical.paneles
#   electrical.inversor
#   electrical.corrientes
#   electrical.protecciones
#   electrical.conductores
#   electrical.nec
#
# ==========================================================
