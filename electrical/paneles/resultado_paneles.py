"""
Contrato del dominio PANELES (generador FV DC).

Este módulo define la SALIDA OFICIAL del motor de paneles.

Ningún módulo externo debe depender de estructuras internas
de cálculo. Todos los módulos consumidores deben utilizar
exclusivamente las clases definidas aquí.

Consumidores típicos:

    energia
    corrientes
    conductores
    protecciones
    ingenieria_electrica
    reportes
    UI

Este contrato representa el estado final del generador FV DC.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any


# =========================================================
# Información eléctrica por MPPT / grupo de strings
# =========================================================

@dataclass
class StringFV:
    """
    Representa un grupo de strings conectado a un MPPT.
    """

    mppt: int

    # configuración
    n_series: int
    n_strings: int

    # -----------------------------------------------------
    # Voltajes
    # -----------------------------------------------------

    vmp_string_v: float
    voc_frio_string_v: float

    # -----------------------------------------------------
    # Corrientes
    # -----------------------------------------------------

    imp_string_a: float      # corriente MPP del string
    i_mppt_a: float          # corriente total hacia MPPT

    # -----------------------------------------------------
    # Corrientes NEC
    # -----------------------------------------------------

    isc_array_a: float       # corriente de cortocircuito total
    imax_pv_a: float         # corriente máxima permitida
    idesign_cont_a: float    # corriente de diseño continua NEC


# =========================================================
# Recomendación del motor de strings
# =========================================================

@dataclass
class RecomendacionStrings:
    """
    Recomendación óptima calculada por el motor de strings.
    """

    n_series: int
    n_strings_total: int
    strings_por_mppt: int

    vmp_string_v: float
    vmp_stc_string_v: float
    voc_frio_string_v: float


# =========================================================
# Información global del generador FV
# =========================================================

@dataclass
class ArrayFV:
    """
    Representa el generador FV completo.
    """

    # -----------------------------------------------------
    # Potencia
    # -----------------------------------------------------

    potencia_dc_w: float

    # -----------------------------------------------------
    # Parámetros eléctricos del array
    # -----------------------------------------------------

    vdc_nom: float
    idc_nom: float

    voc_frio_array_v: float

    # -----------------------------------------------------
    # Configuración física
    # -----------------------------------------------------

    n_strings_total: int
    n_paneles_total: int

    strings_por_mppt: int


# =========================================================
# SALIDA OFICIAL DEL DOMINIO PANELES
# =========================================================

@dataclass
class ResultadoPaneles:
    """
    Resultado final del dominio paneles.

    Este objeto representa el estado completo del generador FV.
    """

    # estado del cálculo
    ok: bool

    # topología del sistema
    topologia: str

    # resumen del generador
    array: ArrayFV

    # recomendación del motor
    recomendacion: RecomendacionStrings

    # detalle eléctrico por MPPT
    strings: List[StringFV]

    # diagnóstico del cálculo
    warnings: List[str]
    errores: List[str]

    # metadatos / trazabilidad
    meta: Dict[str, Any]


# =========================================================
# SALIDAS DEL DOMINIO
# =========================================================

"""
Este módulo produce:

ResultadoPaneles
    ├─ array: ArrayFV
    │      ├─ potencia_dc_w
    │      ├─ vdc_nom
    │      ├─ idc_nom
    │      ├─ voc_frio_array_v
    │      ├─ n_strings_total
    │      ├─ n_paneles_total
    │      └─ strings_por_mppt
    │
    ├─ recomendacion: RecomendacionStrings
    │
    ├─ strings: List[StringFV]
    │      ├─ mppt
    │      ├─ n_series
    │      ├─ n_strings
    │      ├─ vmp_string_v
    │      ├─ voc_frio_string_v
    │      ├─ imp_string_a
    │      ├─ i_mppt_a
    │      ├─ isc_array_a
    │      ├─ imax_pv_a
    │      └─ idesign_cont_a
    │
    ├─ warnings
    ├─ errores
    └─ meta
"""
