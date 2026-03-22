from dataclasses import dataclass
from typing import List


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

    # =========================
    # OK
    # =========================
    @staticmethod
    def build(
        panel: NivelCorriente,
        string: NivelCorriente,
        mppt: NivelCorriente,
        dc_total: NivelCorriente,
        ac: NivelCorriente,
    ):
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
            ac=cero,
            errores=[msg],
            warnings=[],
        )
