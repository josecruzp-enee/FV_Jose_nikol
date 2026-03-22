from __future__ import annotations

"""
PROTECCIONES FV — MÓDULO UNIFICADO (OCPD)

Responsabilidad:
    - Selección de protecciones (NO cálculo de corrientes)

Fuente de verdad:
    - ResultadoCorrientes (corrientes ya con NEC aplicado)

Normativa:
    - NEC 690.8
    - NEC 690.9
    - NEC 210.20(A)
    - NEC 240.6

REGLAS:
    - NO recalcular factores (1.25 ya aplicado)
    - NO usar datos crudos (isc, i_nom, etc.)
    - SOLO usar i_diseno
"""

from dataclasses import dataclass
from typing import Optional


# ==========================================================
# CONTRATO DE CORRIENTES (DEPENDENCIA)
# ==========================================================

@dataclass(frozen=True)
class NivelCorriente:
    i_operacion_a: float
    i_diseno_a: float


@dataclass(frozen=True)
class ResultadoCorrientes:
    panel: NivelCorriente
    string: NivelCorriente
    mppt: NivelCorriente
    dc_total: NivelCorriente
    ac: NivelCorriente


# ==========================================================
# ENTRADA DEL DOMINIO
# ==========================================================

@dataclass(frozen=True)
class EntradaProteccionesFV:
    """
    Entrada del dominio protecciones.

    Fuente de verdad:
        → corrientes ya calculadas
    """

    corrientes: ResultadoCorrientes
    n_strings: int


# ==========================================================
# TABLA NEC 240.6
# ==========================================================

TAMANOS_OCPD_STD = [
    15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 110, 125,
    150, 175, 200, 225, 250, 300,
    350, 400, 450, 500, 600
]


def seleccionar_ocpd(i_diseno: float) -> int:
    """
    Selecciona el siguiente valor estándar NEC ≥ corriente
    """

    if i_diseno <= 0:
        raise ValueError("Corriente inválida para OCPD")

    for size in TAMANOS_OCPD_STD:
        if i_diseno <= size:
            return size

    raise ValueError("Corriente fuera de rango NEC 240.6")


# ==========================================================
# RESULTADOS TIPADOS
# ==========================================================

@dataclass(frozen=True)
class OCPDResultado:
    i_diseno_a: float
    tamano_a: int
    norma: str


@dataclass(frozen=True)
class FusibleStringResultado:
    requerido: bool
    i_diseno_a: Optional[float]
    tamano_a: Optional[int]
    norma: Optional[str]
    nota: Optional[str]


@dataclass(frozen=True)
class ProteccionesFVResultado:
    ok: bool
    errores: list[str]

    ocpd_ac: OCPDResultado
    ocpd_dc_array: OCPDResultado
    fusible_string: FusibleStringResultado


# ==========================================================
# CÁLCULOS
# ==========================================================

def calcular_ocpd_ac(i_diseno_ac: float) -> OCPDResultado:
    """
    Breaker AC del inversor
    NEC 690.8 / 210.20(A)
    """

    size = seleccionar_ocpd(i_diseno_ac)

    return OCPDResultado(
        i_diseno_a=round(i_diseno_ac, 3),
        tamano_a=size,
        norma="NEC 690.8 / 210.20(A)"
    )


def calcular_ocpd_dc_array(i_diseno_dc: float) -> OCPDResultado:
    """
    Protección lado DC (salida combinador / entrada inversor)
    NEC 690.9
    """

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
    """
    Fusible por string (NEC 690.9)

    Regla:
        ≥ 3 strings → obligatorio
    """

    if n_strings < 3:
        return FusibleStringResultado(
            requerido=False,
            i_diseno_a=None,
            tamano_a=None,
            norma=None,
            nota="No requerido (<3 strings en paralelo)"
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
) -> ProteccionesFVResultado:

    errores: list[str] = []

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

        return ProteccionesFVResultado(
            ok=True,
            errores=[],
            ocpd_ac=ocpd_ac,
            ocpd_dc_array=ocpd_dc_array,
            fusible_string=fusible_string
        )

    except Exception as e:

        errores.append(str(e))

        return ProteccionesFVResultado(
            ok=False,
            errores=errores,
            ocpd_ac=None,
            ocpd_dc_array=None,
            fusible_string=None
        )


# ==========================================================
# USO ESPERADO
# ==========================================================
#
# entrada = EntradaProteccionesFV(
#     corrientes=resultado_corrientes,
#     n_strings=numero_strings
# )
#
# resultado = ejecutar_protecciones_fv(entrada)
#
# resultado.ocpd_ac.tamano_a
# resultado.ocpd_dc_array.tamano_a
# resultado.fusible_string.tamano_a
#
# ==========================================================
