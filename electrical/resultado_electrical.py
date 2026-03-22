from __future__ import annotations
from dataclasses import dataclass

from electrical.paneles.resultado_paneles import ResultadoPaneles
from electrical.corrientes.resultado_corrientes import ResultadoCorrientes
from electrical.conductores.resultado_conductores import ResultadoConductores
from electrical.protecciones.resultado_protecciones import ResultadoProtecciones


@dataclass(frozen=True)
class ResultadoElectrico:
    """
    Resultado consolidado del sistema eléctrico FV.
    """

    ok: bool

    paneles: ResultadoPaneles
    corrientes: ResultadoCorrientes
    conductores: ResultadoConductores
    protecciones: ResultadoProtecciones

    errores: list[str]
    warnings: list[str]
