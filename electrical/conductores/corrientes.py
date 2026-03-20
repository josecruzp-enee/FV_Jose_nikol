from __future__ import annotations

"""
SUBDOMINIO CORRIENTES — FV ENGINE
================================

🔷 PROPÓSITO
----------------------------------------------------------
Aplicar factores de diseño (NEC) a corrientes YA calculadas.

Este módulo:
    ✔ NO calcula física base
    ✔ NO reconstruye strings
    ✔ SOLO transforma datos provenientes de ResultadoPaneles

----------------------------------------------------------
🔷 FUENTE DE VERDAD
----------------------------------------------------------

ResultadoPaneles:
    → array.idc_nom     (corriente total DC)
    → array.isc_total   (corriente máxima DC)
    → strings           (corriente por string)
"""

from dataclasses import dataclass
import math
from typing import List

from electrical.paneles.resultado_paneles import ResultadoPaneles


# ==========================================================
# NIVEL DE CORRIENTE
# ==========================================================

@dataclass(frozen=True)
class NivelCorriente:
    """
    Representa una corriente en un nivel del sistema.

    i_operacion_a → corriente real
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

    array = inp.paneles.array
    strings = inp.paneles.strings

    if not strings:
        raise ValueError("No hay strings definidos")

    s0 = strings[0]

    # ---------------- PANEL ----------------
    i_panel_operacion = s0.isc_string_a
    i_panel_diseno = i_panel_operacion * inp.factor_dc

    # ---------------- STRING ----------------
    i_string_operacion = s0.imp_string_a
    i_string_diseno = s0.isc_string_a * inp.factor_dc

    # ---------------- MPPT ----------------
    strings_por_mppt = array.strings_por_mppt

    i_mppt_operacion = s0.imp_string_a * strings_por_mppt
    i_mppt_diseno = (s0.isc_string_a * strings_por_mppt) * inp.factor_dc

    # ---------------- DC TOTAL ----------------
    i_dc_operacion = array.idc_nom
    i_dc_diseno = array.isc_total * inp.factor_dc

    # ---------------- AC ----------------
    p_w = inp.kw_ac * 1000.0

    if inp.vac <= 0 or p_w <= 0:
        i_ac_operacion = 0.0
    else:
        if inp.fases == 3:
            i_ac_operacion = p_w / (math.sqrt(3) * inp.vac * inp.fp)
        else:
            i_ac_operacion = p_w / (inp.vac * inp.fp)

    i_ac_diseno = i_ac_operacion * inp.factor_ac

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
# RESUMEN DE VARIABLES DE SALIDA
# ==========================================================

"""
SALIDA: ResultadoCorrientes
==========================

Cada nivel devuelve un objeto NivelCorriente con:

    i_operacion_a → corriente real del sistema
    i_diseno_a    → corriente con factor NEC aplicado

----------------------------------------------------------

1. PANEL
----------------------------------------------------------
panel.i_operacion_a
    = corriente de corto circuito del módulo (Isc)

panel.i_diseno_a
    = Isc × 1.25 (NEC)

----------------------------------------------------------

2. STRING
----------------------------------------------------------
string.i_operacion_a
    = corriente de operación del string (Imp)

string.i_diseno_a
    = Isc_string × 1.25

----------------------------------------------------------

3. MPPT
----------------------------------------------------------
mppt.i_operacion_a
    = corriente total que entra a un MPPT
    = Imp_string × strings_por_mppt

mppt.i_diseno_a
    = Isc_string × strings_por_mppt × 1.25

----------------------------------------------------------

4. DC TOTAL (GENERADOR FV)
----------------------------------------------------------
dc_total.i_operacion_a
    = corriente total del generador DC
    = array.idc_nom  (VIENE DE PANELES)

dc_total.i_diseno_a
    = corriente máxima DC × 1.25
    = array.isc_total × 1.25

----------------------------------------------------------

5. AC (SALIDA DEL INVERSOR)
----------------------------------------------------------
ac.i_operacion_a
    = corriente AC real del inversor
    = P / (V × fp)  ó  P / (√3 × V × fp)

ac.i_diseno_a
    = corriente AC × 1.25

----------------------------------------------------------

USO DE SALIDAS
----------------------------------------------------------

dc_total → conductores DC
string   → fusibles
mppt     → validación de entrada inversor
ac       → breaker y conductores AC

----------------------------------------------------------

REGLA FINAL
----------------------------------------------------------

Este módulo NO calcula corrientes base.
Solo transforma datos provenientes de ResultadoPaneles.
"""
