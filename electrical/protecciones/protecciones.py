from __future__ import annotations

"""
MÓDULO DE PROTECCIONES FV (OCPD)

Responsabilidades:
    - dimensionar breaker AC de salida de inversor
    - dimensionar fusible de string DC

Normativa base:
    NEC 690.8
    NEC 690.9
    NEC 210.20(A)
    NEC 240.6

Este módulo NO calcula corrientes.
Solo dimensiona dispositivos de protección.
"""

from dataclasses import dataclass
from typing import Optional


# ==========================================================
# TAMAÑOS ESTÁNDAR OCPD (NEC 240.6)
# ==========================================================

TAMANOS_OCPD_STD = [
    15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 110, 125,
    150, 175, 200, 225, 250, 300,
    350, 400, 450, 500, 600
]


def seleccionar_ocpd(i_requerida: float) -> int:

    corriente = float(i_requerida)

    for size in TAMANOS_OCPD_STD:
        if corriente <= size:
            return int(size)

    return TAMANOS_OCPD_STD[-1]


# ==========================================================
# RESULTADOS TIPADOS
# ==========================================================

@dataclass(frozen=True)
class BreakerACResultado:

    i_nom_a: float
    i_diseno_a: float
    tamano_a: int
    factor_aplicado: float
    norma: str


@dataclass(frozen=True)
class FusibleStringResultado:

    requerido: bool

    i_min_a: Optional[float] = None
    tamano_a: Optional[int] = None
    factor_aplicado: Optional[float] = None

    nota: Optional[str] = None
    norma: Optional[str] = None


@dataclass(frozen=True)
class ProteccionesFVResultado:

    breaker_ac: BreakerACResultado
    fusible_string: FusibleStringResultado


# ==========================================================
# BREAKER AC (SALIDA INVERSOR)
# NEC 690.8 + 210.20(A)
# ==========================================================

def calcular_breaker_ac(
    iac_nom_a: float,
    es_carga_continua: bool = True,
    factor_continuo: float = 1.25
) -> BreakerACResultado:

    i_nom = float(iac_nom_a)

    if es_carga_continua:
        i_diseno = i_nom * factor_continuo
    else:
        i_diseno = i_nom

    breaker = seleccionar_ocpd(i_diseno)

    return BreakerACResultado(
        i_nom_a=round(i_nom, 3),
        i_diseno_a=round(i_diseno, 3),
        tamano_a=breaker,
        factor_aplicado=factor_continuo if es_carga_continua else 1.0,
        norma="NEC 690.8 / 210.20(A)"
    )


# ==========================================================
# FUSIBLE DE STRING DC
# NEC 690.9
# ==========================================================

def calcular_fusible_string(
    *,
    n_strings: int,
    isc_mod_a: float,
    has_combiner: Optional[bool] = None,
    aplicar_factor_continuo: bool = True
) -> FusibleStringResultado:

    ns = int(n_strings)

    requiere = bool(has_combiner) if has_combiner is not None else (ns >= 3)

    if not requiere:

        return FusibleStringResultado(
            requerido=False,
            nota="Protección no requerida (<3 strings en paralelo)."
        )

    isc = float(isc_mod_a)

    factor = 1.25

    if aplicar_factor_continuo:
        factor *= 1.25

    i_min = isc * factor

    return FusibleStringResultado(
        requerido=True,
        i_min_a=round(i_min, 3),
        tamano_a=seleccionar_ocpd(i_min),
        factor_aplicado=round(factor, 3),
        norma="NEC 690.9"
    )


# ==========================================================
# ORQUESTADOR PROTECCIONES FV
# ==========================================================

def dimensionar_protecciones_fv(
    *,
    iac_nom_a: float,
    n_strings: int,
    isc_mod_a: float,
    has_combiner: Optional[bool] = None
) -> ProteccionesFVResultado:

    breaker_ac = calcular_breaker_ac(iac_nom_a)

    fusible_string = calcular_fusible_string(
        n_strings=n_strings,
        isc_mod_a=isc_mod_a,
        has_combiner=has_combiner
    )

    return ProteccionesFVResultado(
        breaker_ac=breaker_ac,
        fusible_string=fusible_string
    )


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# dimensionar_protecciones_fv()
#
# Entrada:
#   iac_nom_a
#   n_strings
#   isc_mod_a
#
# Salida:
#   ProteccionesFVResultado
#
# Campos:
#   breaker_ac
#   fusible_string
#
# Consumido por:
#   electrical.paquete_nec
#
# ==========================================================
