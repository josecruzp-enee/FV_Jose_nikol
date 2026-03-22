    from __future__ import annotations

from dataclasses import dataclass
from typing import List
import math

from electrical.paneles.resultado_paneles import ResultadoPaneles


# ==========================================================
# MODELOS
# ==========================================================

@dataclass(frozen=True)
class NivelCorriente:
    i_operacion_a: float
    i_diseno_a: float


@dataclass(frozen=True)
class ResultadoCorrientes:

    ok: bool

    panel: NivelCorriente
    string: NivelCorriente
    mppt: NivelCorriente
    dc_total: NivelCorriente
    ac: NivelCorriente

    errores: List[str]
    warnings: List[str]

    @staticmethod
    def build(
        panel: NivelCorriente,
        string: NivelCorriente,
        mppt: NivelCorriente,
        dc_total: NivelCorriente,
        ac: NivelCorriente,
    ) -> "ResultadoCorrientes":
        return ResultadoCorrientes(
            ok=True,
            panel=panel,
            string=string,
            mppt=mppt,
            dc_total=dc_total,
            ac=ac,
            errores=[],
            warnings=[],
        )

    @staticmethod
    def error(msg: str) -> "ResultadoCorrientes":
        cero = NivelCorriente(0.0, 0.0)

        return ResultadoCorrientes(
            ok=False,
            panel=cero,
            string=cero,
            mppt=cero,
            dc_total=cero,
            ac=cero,
            errores=[msg],
            warnings=[],
        )


# ==========================================================
# INPUT
# ==========================================================

@dataclass(frozen=True)
class CorrientesInput:
    paneles: ResultadoPaneles
    kw_ac: float
    vac: float
    fases: int
    fp: float

    factor_dc: float = 1.25
    factor_ac: float = 1.25


# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def calcular_corrientes(inp: CorrientesInput) -> ResultadoCorrientes:

    paneles = inp.paneles
    array = paneles.array
    strings = paneles.strings

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------
    if not strings:
        return ResultadoCorrientes.error("No hay strings definidos")

    if array.n_strings_total <= 0:
        return ResultadoCorrientes.error("n_strings_total inválido")

    s0 = strings[0]

    FACTOR_DC = inp.factor_dc
    FACTOR_AC = inp.factor_ac

    # ------------------------------------------------------
    # PANEL
    # ------------------------------------------------------
    i_panel_operacion = s0.isc_string_a
    i_panel_diseno = i_panel_operacion * FACTOR_DC

    panel = NivelCorriente(i_panel_operacion, i_panel_diseno)

    # ------------------------------------------------------
    # STRING
    # ------------------------------------------------------
    i_string_operacion = s0.imp_string_a
    i_string_diseno = s0.isc_string_a * FACTOR_DC

    string = NivelCorriente(i_string_operacion, i_string_diseno)

    # ------------------------------------------------------
    # MPPT
    # ------------------------------------------------------
    strings_por_mppt = max(1, array.strings_por_mppt)

    i_mppt_operacion = s0.imp_string_a * strings_por_mppt
    i_mppt_diseno = (s0.isc_string_a * strings_por_mppt) * FACTOR_DC

    mppt = NivelCorriente(i_mppt_operacion, i_mppt_diseno)

    # ------------------------------------------------------
    # DC TOTAL
    # ------------------------------------------------------
    i_dc_operacion = array.idc_nom
    i_dc_diseno = array.isc_total * FACTOR_DC

    dc_total = NivelCorriente(i_dc_operacion, i_dc_diseno)

    # ------------------------------------------------------
    # AC
    # ------------------------------------------------------
    p_w = inp.kw_ac * 1000.0

    if inp.vac <= 0 or p_w <= 0:
        return ResultadoCorrientes.error("Datos AC inválidos")

    if inp.fases == 3:
        i_ac_operacion = p_w / (math.sqrt(3) * inp.vac * inp.fp)
    else:
        i_ac_operacion = p_w / (inp.vac * inp.fp)

    i_ac_diseno = i_ac_operacion * FACTOR_AC

    ac = NivelCorriente(i_ac_operacion, i_ac_diseno)

    # ------------------------------------------------------
    # RESULTADO FINAL
    # ------------------------------------------------------
    return ResultadoCorrientes.build(
        panel=panel,
        string=string,
        mppt=mppt,
        dc_total=dc_total,
        ac=ac,
    )
