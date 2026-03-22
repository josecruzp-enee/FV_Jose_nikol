from dataclasses import dataclass
from typing import List

from electrical.conductores.corrientes import ResultadoCorrientes
from electrical.protecciones.protecciones import ProteccionesFVResultado
from electrical.conductores.calculo_conductores import TramosFV


@dataclass(frozen=True)
class ResultadoElectrical:

    ok: bool
    errores: List[str]
    warnings: List[str]

    corrientes: ResultadoCorrientes
    protecciones: ProteccionesFVResultado
    conductores: TramosFV
