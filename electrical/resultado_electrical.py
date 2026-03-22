from __future__ import annotations

from dataclasses import dataclass
from typing import List

from electrical.conductores.corrientes import ResultadoCorrientes
from electrical.protecciones.protecciones import ProteccionesFVResultado
from electrical.conductores.calculo_conductores import TramosFV


@dataclass(frozen=True)
class ResultadoElectrical:
    """
    Resultado global del dominio electrical.

    Es la fuente única de verdad para:
        - corrientes
        - protecciones
        - conductores
    """

    ok: bool
    errores: List[str]
    warnings: List[str]

    corrientes: ResultadoCorrientes
    protecciones: ProteccionesFVResultado
    conductores: TramosFV
