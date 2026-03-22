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
from typing import Optional


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

    errores: list[str]
    warnings: list[str]

    ocpd_ac: OCPDResultado
    ocpd_dc_array: OCPDResultado
    fusible_string: FusibleStringResultado
