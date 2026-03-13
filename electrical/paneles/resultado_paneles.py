"""
CONTRATO DEL DOMINIO PANELES — FV ENGINE

Este módulo define la SALIDA OFICIAL del motor del generador FV DC.

Regla arquitectónica:
---------------------

Ningún módulo externo debe depender de estructuras internas
de cálculo del dominio paneles.

Todos los módulos consumidores deben utilizar exclusivamente
las clases definidas en este contrato.

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
# INFORMACIÓN ELÉCTRICA POR MPPT / GRUPO DE STRINGS
# =========================================================

@dataclass
class StringFV:
    """
    Representa un grupo de strings conectado a un MPPT.

    Cada instancia describe el comportamiento eléctrico de
    un conjunto de strings en paralelo que alimentan un MPPT.
    """

    # -----------------------------------------------------
    # Identificación
    # -----------------------------------------------------

    mppt: int

    # -----------------------------------------------------
    # Configuración física
    # -----------------------------------------------------

    n_series: int
    n_strings: int

    # -----------------------------------------------------
    # Voltajes del string
    # -----------------------------------------------------

    vmp_string_v: float
    voc_frio_string_v: float

    # -----------------------------------------------------
    # Corrientes base
    # -----------------------------------------------------

    imp_string_a: float
    isc_panel_a: float

    # corriente total hacia el MPPT
    i_mppt_a: float

    # -----------------------------------------------------
    # Corrientes NEC
    # -----------------------------------------------------

    isc_mppt_a: float
    imax_pv_a: float
    idesign_cont_a: float


# =========================================================
# RECOMENDACIÓN DEL MOTOR DE STRINGS
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
# INFORMACIÓN GLOBAL DEL GENERADOR FV
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
    n_mppt: int

    # -----------------------------------------------------
    # Información del módulo FV
    # -----------------------------------------------------

    p_panel_w: float


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
Este módulo produce un único objeto:

ResultadoPaneles


Estructura:

ResultadoPaneles
    ├─ array: ArrayFV
    │      ├─ potencia_dc_w
    │      ├─ vdc_nom
    │      ├─ idc_nom
    │      ├─ voc_frio_array_v
    │      ├─ n_strings_total
    │      ├─ n_paneles_total
    │      ├─ strings_por_mppt
    │      ├─ n_mppt
    │      └─ p_panel_w
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
    │      ├─ isc_panel_a
    │      ├─ i_mppt_a
    │      ├─ isc_mppt_a
    │      ├─ imax_pv_a
    │      └─ idesign_cont_a
    │
    ├─ warnings
    ├─ errores
    └─ meta
"""
