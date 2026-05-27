from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import math
from collections import defaultdict

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
    ac_inversor: NivelCorriente
    ac_total: NivelCorriente
    ac: NivelCorriente

    mppt_detalle: List[NivelCorriente]
    strings_detalle: List[NivelCorriente]
    inversores_detalle: List[NivelCorriente]
    errores: List[str]
    warnings: List[str]

    # =========================
    # OK
    # =========================
    @staticmethod
    def build(
        panel: NivelCorriente,
        string: NivelCorriente,
        mppt: NivelCorriente,
        dc_total: NivelCorriente,
        ac_inversor: NivelCorriente,
        ac_total: NivelCorriente,
        ac: NivelCorriente,
        mppt_detalle: Optional[List[NivelCorriente]] = None,
        strings_detalle: Optional[List[NivelCorriente]] = None,
        inversores_detalle: Optional[List[NivelCorriente]] = None,
    ):
        return ResultadoCorrientes(
            ok=True,
            panel=panel,
            string=string,
            mppt=mppt,
            dc_total=dc_total,
            ac_inversor=ac_inversor,
            ac_total=ac_total,
            ac=ac,
            mppt_detalle=mppt_detalle or [],
            strings_detalle=strings_detalle or [],
            errores=[],
            warnings=[],
            inversores_detalle=inversores_detalle or [],
        )

    # =========================
    # ERROR
    # =========================
    @staticmethod
    def error(msg: str):
        cero = NivelCorriente(0.0, 0.0)
        return ResultadoCorrientes(
            ok=False,
            panel=cero,
            string=cero,
            mppt=cero,
            dc_total=cero,
            ac_inversor=cero,
            ac_total=cero,
            ac=cero,
            mppt_detalle=[],
            strings_detalle=[],
            errores=[msg],
            warnings=[],
            inversores_detalle=[],
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
    n_inversores: int = 1
    
    factor_dc: float = 1.25
    factor_ac: float = 1.25


# ==========================================================
# 🔥 DEBUG AGRUPACIÓN MPPT
# ==========================================================

def _agrupar_por_mppt(strings):

    grupos = defaultdict(list)

    for s in strings:

        inv = getattr(s, "inversor", None)
        mppt = getattr(s, "mppt", None)

        if inv is None:
            raise ValueError("String sin inversor")

        if mppt is None:
            raise ValueError("String sin MPPT")

        grupos[(inv, mppt)].append(s)

    return grupos

# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def calcular_corrientes(inp: CorrientesInput) -> ResultadoCorrientes:

    print("\n########################################")
    print("🔥 DEBUG CORRIENTES INICIO")
    print("########################################")

    paneles = inp.paneles
    array = paneles.array
    strings = paneles.strings

    print("Total strings:", len(strings))
    print("n_strings_total:", getattr(array, "n_strings_total", "N/A"))

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

    print("\n🔹 PANEL")
    print("I operación:", i_panel_operacion)
    print("I diseño:", i_panel_diseno)

    panel = NivelCorriente(i_panel_operacion, i_panel_diseno)

    # ------------------------------------------------------
    # STRING
    # ------------------------------------------------------
    i_string_operacion = s0.imp_string_a
    i_string_diseno = s0.isc_string_a * FACTOR_DC

    print("\n🔹 STRING")
    print("I operación:", i_string_operacion)
    print("I diseño:", i_string_diseno)

    string = NivelCorriente(i_string_operacion, i_string_diseno)

    # ======================================================
    # 🔥 MPPT REAL
    # ======================================================
    grupos = _agrupar_por_mppt(strings)

    mppt_detalle = []

    print("\n🔹 CÁLCULO MPPT")

    for (inv_id, mppt_id), grupo in grupos.items():
        i_operacion = sum(s.imp_string_a for s in grupo)
        i_diseno = sum(s.isc_string_a for s in grupo) * FACTOR_DC

        print(f"INV {inv_id} / MPPT {mppt_id}:")
        print("  strings:", len(grupo))
        print("  I operación:", i_operacion)
        print("  I diseño:", i_diseno)

        mppt_detalle.append(NivelCorriente(i_operacion, i_diseno))

    print("\nLEN mppt_detalle:", len(mppt_detalle))

    # ------------------------------------------------------
    # MPPT (compatibilidad)
    # ------------------------------------------------------
    mppt = (
        max(mppt_detalle, key=lambda x: x.i_diseno_a)
        if mppt_detalle else NivelCorriente(0.0, 0.0)
    )

    # ------------------------------------------------------
    # DC TOTAL
    # ------------------------------------------------------
    i_dc_operacion = sum(m.i_operacion_a for m in mppt_detalle)
    i_dc_diseno = sum(m.i_diseno_a for m in mppt_detalle)

    print("\n🔹 DC TOTAL")
    print("I operación:", i_dc_operacion)
    print("I diseño:", i_dc_diseno)

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

    print("\n🔹 AC")
    print("I operación:", i_ac_operacion)
    print("I diseño:", i_ac_diseno)

    ac = NivelCorriente(i_ac_operacion, i_ac_diseno)
    ac_total = ac
    
    n_inv = max(int(getattr(inp, "n_inversores", 1) or 1), 1)

    ac_inversor = NivelCorriente(
        i_operacion_a=ac.i_operacion_a / n_inv,
        i_diseno_a=ac.i_diseno_a / n_inv,
    )
    inversores_detalle = [
        NivelCorriente(
            i_operacion_a=ac_inversor.i_operacion_a,
            i_diseno_a=ac_inversor.i_diseno_a,
        )
        for _ in range(n_inv)
    ]
    print("\n########################################")
    print("🔥 DEBUG CORRIENTES FIN")
    print("########################################\n")

    # ------------------------------------------------------
    # RESULTADO FINAL
    # ------------------------------------------------------
    return ResultadoCorrientes.build(
        panel=panel,
        string=string,
        mppt=mppt,
        dc_total=dc_total,
        ac_inversor=ac_inversor,
        ac_total=ac_total,
        ac=ac,
        mppt_detalle=mppt_detalle,
        strings_detalle=strings,
        inversores_detalle=inversores_detalle,
    )


# ==========================================================
# RESUMEN TÉCNICO DEL MÓDULO
# ==========================================================
#
# Este módulo calcula las corrientes eléctricas principales del sistema FV.
#
# Entradas principales:
# - paneles: resultado del dimensionamiento de paneles y strings.
# - kw_ac: potencia AC total del sistema.
# - vac: voltaje AC del sistema.
# - fases: 1 o 3.
# - fp: factor de potencia.
# - n_inversores: cantidad de inversores.
# - factor_dc: factor de diseño DC, normalmente 1.25.
# - factor_ac: factor de diseño AC, normalmente 1.25.
#
# Salidas principales:
# - panel: corriente de un panel.
# - string: corriente de un string.
# - mppt: MPPT crítico, es decir, el de mayor corriente de diseño.
# - dc_total: suma de todos los MPPT.
# - ac_inversor: corriente AC de diseño por cada inversor.
# - ac_total / ac: corriente AC total del sistema.
# - mppt_detalle: lista de corrientes por cada MPPT real.
# - inversores_detalle: lista de corrientes AC individuales por inversor.
#
# Criterio importante:
# - Los strings en paralelo dentro de un mismo MPPT suman corriente.
# - Cada MPPT se calcula agrupando por (inversor, mppt).
# - La corriente AC total se divide entre n_inversores para obtener ac_inversor.
# - inversores_detalle permite dimensionar conductores y protecciones
#   separados para cada salida de inversor.
#
# Este módulo NO selecciona calibres, protecciones ni canalizaciones.
# Solo calcula corrientes. El dimensionamiento de conductores debe hacerse
# en el módulo de conductores usando mppt_detalle e inversores_detalle.
# ==========================================================
