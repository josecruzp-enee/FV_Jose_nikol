from __future__ import annotations

"""
RESULTADO DE CORRIENTES — FV ENGINE
==================================

🔷 PROPÓSITO
----------------------------------------------------------
Representar las corrientes del sistema fotovoltaico
en diferentes niveles eléctricos.

Este archivo:

    ✔ NO calcula
    ✔ NO transforma
    ✔ SOLO almacena resultados

----------------------------------------------------------
🔷 FUENTE DE DATOS
----------------------------------------------------------

Proviene de:

    electrical.conductores.corrientes.calcular_corrientes

----------------------------------------------------------
🔷 PRINCIPIO
----------------------------------------------------------

Paneles define la física  
Corrientes aplica normativa (NEC)  
Conductores usa estos resultados
"""

from dataclasses import dataclass


# ==========================================================
# NIVEL DE CORRIENTE
# ==========================================================

@dataclass(frozen=True)
class NivelCorriente:
    """
    Corriente en un nivel eléctrico del sistema FV.

    i_operacion_a:
        → corriente real del sistema

    i_diseno_a:
        → corriente ajustada con factor NEC
    """

    i_operacion_a: float
    i_diseno_a: float


# ==========================================================
# RESULTADO DE CORRIENTES FV
# ==========================================================

@dataclass(frozen=True)
class ResultadoCorrientes:
    """
    Corrientes del sistema FV separadas por nivel eléctrico.

    NIVELES:

    panel:
        → corriente a nivel módulo (referencial)

    string:
        → corriente de un string

    mppt:
        → corriente hacia un MPPT

    dc_total:
        → corriente total del generador FV

    ac:
        → corriente de salida del inversor
    """

    panel: NivelCorriente
    string: NivelCorriente
    mppt: NivelCorriente
    dc_total: NivelCorriente
    ac: NivelCorriente


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# OBJETO PRINCIPAL:
# ----------------------------------------------------------
# ResultadoCorrientes
#
#
# ----------------------------------------------------------
# ENTRADA (IMPLÍCITA)
# ----------------------------------------------------------
#
# Este archivo NO recibe entrada directa.
#
# Es construido por:
#
#   calcular_corrientes()
#
#
# ----------------------------------------------------------
# VARIABLES CLAVE
# ----------------------------------------------------------
#
# dc_total.i_operacion_a
#     → corriente total DC del sistema
#
# dc_total.i_diseno_a
#     → corriente DC con factor NEC
#
# ac.i_operacion_a
#     → corriente AC del inversor
#
# ac.i_diseno_a
#     → corriente AC con factor NEC
#
#
# ----------------------------------------------------------
# USO EN FV ENGINE
# ----------------------------------------------------------
#
# ResultadoPaneles
#       ↓
# calcular_corrientes
#       ↓
# ResultadoCorrientes  ← ESTE ARCHIVO
#       ↓
# conductores
#       ↓
# protecciones
#
#
# ----------------------------------------------------------
# PRINCIPIO
# ----------------------------------------------------------
#
# Este objeto es la fuente de verdad para el dimensionamiento
# de conductores y protecciones.
#
# Ningún módulo debe recalcular estas corrientes.
#
# ==========================================================
