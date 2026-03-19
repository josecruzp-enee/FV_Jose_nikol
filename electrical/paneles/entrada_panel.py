from __future__ import annotations

"""
CONTRATO DE ENTRADA — DOMINIO PANELES

Define la estructura de datos que recibe el dominio paneles.

Reglas:
- Este módulo NO contiene lógica de cálculo
- Solo define el contrato de entrada
- Es inmutable (frozen=True)
- Valida consistencia mínima

Consumido por:
    electrical.paneles.orquestador_paneles
"""
from __future__ import annotations

"""
SALIDA PÚBLICA DEL DOMINIO PANELES — FV ENGINE
=============================================

Este módulo representa la INTERFAZ OFICIAL hacia el exterior.

Consumido por:
    - core.aplicacion
    - energy (8760)
    - conductores
    - protecciones
    - reportes
    - UI

Reglas:
    - No contiene lógica
    - No redefine modelos
    - Solo expone datos necesarios
"""

from dataclasses import dataclass
from typing import List


# =========================================================
# RESUMEN DEL ARRAY FV (EXTERNO)
# =========================================================

@dataclass(frozen=True)
class ArrayFVOut:
    """
    Vista simplificada del generador FV para otros dominios.
    """

    potencia_dc_w: float
    vdc_nom: float
    idc_nom: float

    n_strings_total: int
    n_paneles_total: int

    strings_por_mppt: int
    n_mppt: int


# =========================================================
# STRING FV (EXTERNO)
# =========================================================

@dataclass(frozen=True)
class StringFVOut:
    """
    Información necesaria para downstream (conductores, protecciones).
    """

    mppt: int
    n_series: int
    n_strings: int

    vmp_string_v: float
    voc_frio_string_v: float

    imp_string_a: float
    isc_string_a: float

    i_mppt_a: float
    isc_mppt_a: float
    idesign_cont_a: float


# =========================================================
# RESULTADO PÚBLICO DEL DOMINIO
# =========================================================

@dataclass(frozen=True)
class ResultadoPanelesOut:
    """
    Objeto que consumen los otros dominios.

    Este es el único punto de entrada al dominio paneles.
    """

    ok: bool

    array: ArrayFVOut
    strings: List[StringFVOut]

    warnings: List[str]
    errores: List[str]
