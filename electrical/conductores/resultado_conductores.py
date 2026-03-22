from dataclasses import dataclass
from typing import List

from electrical.conductores.calculo_conductores import TramosFV


@dataclass(frozen=True)
class ResultadoConductores:

    ok: bool

    tramos: TramosFV

    errores: List[str]
    warnings: List[str]

    @staticmethod
    def build(tramos: TramosFV):
        return ResultadoConductores(
            ok=True,
            tramos=tramos,
            errores=[],
            warnings=[],
        )

    @staticmethod
    def error(msg: str):
        return ResultadoConductores(
            ok=False,
            tramos=None,
            errores=[msg],
            warnings=[],
        )
