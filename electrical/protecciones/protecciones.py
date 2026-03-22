from __future__ import annotations

"""
PROTECCIONES FV — MÓDULO UNIFICADO (OCPD)

Responsabilidad:
    - Selección de protecciones (NO cálculo de corrientes)

Fuente de verdad:
    - ResultadoCorrientes (corrientes ya con NEC aplicado)

REGLAS:
    - SOLO usar i_diseno
"""

from dataclasses import dataclass

from electrical.conductores.corrientes import ResultadoCorrientes

from electrical.protecciones.resultado_protecciones import (
    ResultadoProtecciones,
    OCPDResultado,
    FusibleStringResultado,
)


# ==========================================================
# ENTRADA
# ==========================================================

@dataclass(frozen=True)
class EntradaProteccionesFV:
    corrientes: ResultadoCorrientes
    n_strings: int


# ==========================================================
# TABLA NEC
# ==========================================================

TAMANOS_OCPD_STD = [
    15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 110, 125,
    150, 175, 200, 225, 250, 300,
    350, 400, 450, 500, 600
]


def seleccionar_ocpd(i_diseno: float) -> int:

    if i_diseno <= 0:
        raise ValueError("Corriente inválida para OCPD")

    for size in TAMANOS_OCPD_STD:
        if i_diseno <= size:
            return size

    raise ValueError("Corriente fuera de rango NEC 240.6")


# ==========================================================
# CÁLCULOS
# ==========================================================

def calcular_ocpd_ac(i_diseno_ac: float) -> OCPDResultado:

    size = seleccionar_ocpd(i_diseno_ac)

    return OCPDResultado(
        i_diseno_a=round(i_diseno_ac, 3),
        tamano_a=size,
        norma="NEC 690.8 / 210.20(A)"
    )


def calcular_ocpd_dc_array(i_diseno_dc: float) -> OCPDResultado:

    size = seleccionar_ocpd(i_diseno_dc)

    return OCPDResultado(
        i_diseno_a=round(i_diseno_dc, 3),
        tamano_a=size,
        norma="NEC 690.9"
    )


def calcular_fusible_string(
    n_strings: int,
    i_diseno_string: float
) -> FusibleStringResultado:

    if n_strings < 3:
        return FusibleStringResultado(
            requerido=False,
            i_diseno_a=None,
            tamano_a=None,
            norma=None,
            nota="No requerido (<3 strings)"
        )

    size = seleccionar_ocpd(i_diseno_string)

    return FusibleStringResultado(
        requerido=True,
        i_diseno_a=round(i_diseno_string, 3),
        tamano_a=size,
        norma="NEC 690.9",
        nota=None
    )


# ==========================================================
# ORQUESTADOR
# ==========================================================

def ejecutar_protecciones_fv(
    entrada: EntradaProteccionesFV
) -> ResultadoProtecciones:

    errores: list[str] = []
    warnings: list[str] = []

    try:
        corr = entrada.corrientes

        ocpd_ac = calcular_ocpd_ac(
            corr.ac.i_diseno_a
        )

        ocpd_dc_array = calcular_ocpd_dc_array(
            corr.dc_total.i_diseno_a
        )

        fusible_string = calcular_fusible_string(
            entrada.n_strings,
            corr.string.i_diseno_a
        )

        return ResultadoProtecciones(
            ok=True,
            errores=[],
            warnings=warnings,
            ocpd_ac=ocpd_ac,
            ocpd_dc_array=ocpd_dc_array,
            fusible_string=fusible_string
        )

    except Exception as e:

        errores.append(str(e))

        # fallback seguro (NO None)
        return ResultadoProtecciones(
            ok=False,
            errores=errores,
            warnings=warnings,
            ocpd_ac=OCPDResultado(0.0, 0, ""),
            ocpd_dc_array=OCPDResultado(0.0, 0, ""),
            fusible_string=FusibleStringResultado(
                False, None, None, None, "error"
            )
        )
