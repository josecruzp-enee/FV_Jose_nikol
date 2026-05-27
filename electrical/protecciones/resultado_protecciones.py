from __future__ import annotations

"""
RESULTADO DEL DOMINIO PROTECCIONES — FV ENGINE

Responsabilidad:
    - Definir la salida del dominio protecciones

REGLAS:
    - NO calcula
    - NO usa lógica
    - SOLO representa resultados
"""

from dataclasses import dataclass
from typing import Optional, List


# =========================================================
# OCPD (BREAKERS)
# =========================================================

@dataclass(frozen=True)
class OCPDResultado:
    """
    Resultado de un dispositivo de protección (breaker/fusible).
    """

    i_diseno_a: float
    tamano_a: int
    norma: str


# =========================================================
# FUSIBLE POR STRING
# =========================================================

@dataclass(frozen=True)
class FusibleStringResultado:
    """
    Protección individual por string.
    """

    requerido: bool
    i_diseno_a: Optional[float]
    tamano_a: Optional[int]
    norma: Optional[str]
    nota: Optional[str]


# =========================================================
# RESULTADO GLOBAL
# =========================================================

@dataclass(frozen=True)
class ResultadoProtecciones:
    """
    Resultado completo del dominio protecciones.
    """

    ok: bool

    errores: List[str]
    warnings: List[str]

    # Compatibilidad histórica:
    # representa la protección AC principal / total.
    ocpd_ac: OCPDResultado

    # Nuevo modelo AC separado:
    # - uno por salida de inversor
    # - uno principal del sistema
    ocpd_ac_inversores: List[OCPDResultado]
    ocpd_ac_principal: OCPDResultado

    ocpd_dc_array: OCPDResultado
    fusible_string: FusibleStringResultado

    # Protecciones por MPPT
    mppt: List[OCPDResultado]

    # Fusibles por MPPT
    fusible_mppt: Optional[List[FusibleStringResultado]] = None

    # =====================================================
    # FACTORY DE ERROR (NECESARIO PARA ORQUESTADOR)
    # =====================================================
    @staticmethod
    def error(msg: str) -> "ResultadoProtecciones":
        cero_ocpd = OCPDResultado(0.0, 0, "")

        return ResultadoProtecciones(
            ok=False,
            errores=[msg],
            warnings=[],

            ocpd_ac=cero_ocpd,
            ocpd_ac_inversores=[],
            ocpd_ac_principal=cero_ocpd,

            ocpd_dc_array=cero_ocpd,
            fusible_string=FusibleStringResultado(
                False, None, None, None, "error"
            ),
            mppt=[],
            fusible_mppt=[],
        )
