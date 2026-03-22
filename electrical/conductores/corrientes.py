from __future__ import annotations

"""
SUBDOMINIO CORRIENTES — FV ENGINE
================================

🔷 PROPÓSITO
----------------------------------------------------------
Aplicar factores de diseño (NEC) a corrientes YA calculadas
en el dominio paneles.

Este módulo:

    ✔ NO calcula física base
    ✔ NO reconstruye strings
    ✔ NO usa dict
    ✔ SOLO transforma datos provenientes de ResultadoPaneles

----------------------------------------------------------
🔷 FUENTE DE VERDAD
----------------------------------------------------------

ResultadoPaneles:

    → array.idc_nom       (corriente total DC)
    → array.isc_total     (corriente máxima DC)
    → array.strings_por_mppt
    → strings             (corriente por string)

----------------------------------------------------------
🔷 PRINCIPIO
----------------------------------------------------------

Paneles define la física
Corrientes aplica normativa (NEC)
"""

from dataclasses import dataclass
import math

from electrical.paneles.resultado_paneles import ResultadoPaneles


# ==========================================================
# NIVEL DE CORRIENTE
# ==========================================================

@dataclass(frozen=True)
class NivelCorriente:
    """
    Representa una corriente en un nivel del sistema.

    i_operacion_a → corriente real del sistema
    i_diseno_a    → corriente con factor NEC aplicado
    """

    i_operacion_a: float
    i_diseno_a: float


# ==========================================================
# RESULTADO FINAL
# ==========================================================

@dataclass(frozen=True)
class ResultadoCorrientes:
    """
    Corrientes del sistema FV separadas por nivel eléctrico.
    """

    panel: NivelCorriente
    string: NivelCorriente
    mppt: NivelCorriente
    dc_total: NivelCorriente
    ac: NivelCorriente


# ==========================================================
# ENTRADA TIPADA
# ==========================================================

@dataclass(frozen=True)
class CorrientesInput:
    """
    VARIABLES DE ENTRADA

    paneles:
        → ResultadoPaneles (fuente completa DC)

    kw_ac:
        → potencia del inversor [kW]

    vac:
        → voltaje AC [V]

    fases:
        → 1 o 3

    fp:
        → factor de potencia

    factor_dc:
        → factor NEC DC (default 1.25)

    factor_ac:
        → factor NEC AC (default 1.25)
    """

    paneles: ResultadoPaneles

    kw_ac: float
    vac: float
    fases: int = 1
    fp: float = 1.0

    factor_dc: float = 1.25
    factor_ac: float = 1.25


# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def calcular_corrientes(inp: CorrientesInput) -> ResultadoCorrientes:
    """
    Calcula corrientes del sistema FV a partir de ResultadoPaneles.

    Aplica factores NEC sobre valores ya calculados.

    NO modifica la física base.
    """

    paneles = inp.paneles
    array = paneles.array
    strings = paneles.strings

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if not strings:
        raise ValueError("No hay strings definidos")

    if array.n_strings_total <= 0:
        raise ValueError("n_strings_total inválido")

    s0 = strings[0]

    # ------------------------------------------------------
    # FACTORES NEC
    # ------------------------------------------------------

    FACTOR_DC = inp.factor_dc
    FACTOR_AC = inp.factor_ac

    # ------------------------------------------------------
    # PANEL (referencial)
    # ------------------------------------------------------

    # Se toma el primer string como referencia del módulo
    i_panel_operacion = s0.isc_string_a
    i_panel_diseno = i_panel_operacion * FACTOR_DC

    # ------------------------------------------------------
    # STRING
    # ------------------------------------------------------

    i_string_operacion = s0.imp_string_a
    i_string_diseno = s0.isc_string_a * FACTOR_DC

    # ------------------------------------------------------
    # MPPT
    # ------------------------------------------------------

    strings_por_mppt = max(1, array.strings_por_mppt)

    i_mppt_operacion = s0.imp_string_a * strings_por_mppt
    i_mppt_diseno = (s0.isc_string_a * strings_por_mppt) * FACTOR_DC

    # ------------------------------------------------------
    # DC TOTAL (GENERADOR FV)
    # ------------------------------------------------------

    i_dc_operacion = array.idc_nom
    i_dc_diseno = array.isc_total * FACTOR_DC

    # ------------------------------------------------------
    # AC (SALIDA DEL INVERSOR)
    # ------------------------------------------------------

    p_w = inp.kw_ac * 1000.0

    if inp.vac <= 0 or p_w <= 0:
        i_ac_operacion = 0.0
    else:
        if inp.fases == 3:
            i_ac_operacion = p_w / (math.sqrt(3) * inp.vac * inp.fp)
        else:
            i_ac_operacion = p_w / (inp.vac * inp.fp)

    i_ac_diseno = i_ac_operacion * FACTOR_AC

    # ------------------------------------------------------
    # RESULTADO FINAL
    # ------------------------------------------------------

    return ResultadoCorrientes(

        panel=NivelCorriente(
            i_operacion_a=i_panel_operacion,
            i_diseno_a=i_panel_diseno,
        ),

        string=NivelCorriente(
            i_operacion_a=i_string_operacion,
            i_diseno_a=i_string_diseno,
        ),

        mppt=NivelCorriente(
            i_operacion_a=i_mppt_operacion,
            i_diseno_a=i_mppt_diseno,
        ),

        dc_total=NivelCorriente(
            i_operacion_a=i_dc_operacion,
            i_diseno_a=i_dc_diseno,
        ),

        ac=NivelCorriente(
            i_operacion_a=i_ac_operacion,
            i_diseno_a=i_ac_diseno,
        ),
    )


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# FUNCIÓN PRINCIPAL:
# ----------------------------------------------------------
# calcular_corrientes(inp: CorrientesInput)
#
#
# ----------------------------------------------------------
# ENTRADA
# ----------------------------------------------------------
#
# CorrientesInput:
#
#   paneles: ResultadoPaneles
#       → fuente de verdad del sistema FV
#
#   kw_ac: float
#       → potencia del inversor [kW]
#
#   vac: float
#       → voltaje AC [V]
#
#   fases: int
#       → 1 o 3
#
#   fp: float
#       → factor de potencia
#
#
# ----------------------------------------------------------
# PROCESO
# ----------------------------------------------------------
#
# 1. Lee datos desde ResultadoPaneles
#
# 2. Calcula corrientes en niveles:
#       - panel
#       - string
#       - MPPT
#       - DC total
#       - AC
#
# 3. Aplica factores NEC (1.25 por defecto)
#
#
# ----------------------------------------------------------
# VARIABLES CLAVE
# ----------------------------------------------------------
#
# i_dc_operacion
#       → corriente total DC
#
# i_dc_diseno
#       → corriente DC con NEC
#
# i_ac_operacion
#       → corriente AC del inversor
#
# i_ac_diseno
#       → corriente AC con NEC
#
#
# ----------------------------------------------------------
# SALIDA
# ----------------------------------------------------------
#
# ResultadoCorrientes:
#
#   panel
#   string
#   mppt
#   dc_total
#   ac
#
#
# ----------------------------------------------------------
# UBICACIÓN EN FLUJO
# ----------------------------------------------------------
#
# ResultadoPaneles
#       ↓
# calcular_corrientes   ← ESTE MÓDULO
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
# Este módulo NO define el sistema.
#
# SOLO aplica normativa sobre resultados existentes.
#
# ==========================================================
