from dataclasses import dataclass, asdict
from typing import Any

from core.dominio.contrato import (
    ResultadoProyecto,
    ResultadoSizing,
    ResultadoStrings,
    ResultadoNEC,
    ResultadoFinanciero,
)

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
    PuertoFinanzas,
)


@dataclass
class DependenciasEstudio:
    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    nec: PuertoNEC
    finanzas: PuertoFinanzas


def ejecutar_estudio(datos: Any, deps: DependenciasEstudio):
    # 🔹 Ejecución de casos de uso
    sizing_raw = deps.sizing.ejecutar(datos)
    strings_raw = deps.paneles.ejecutar(datos, sizing_raw)
    energia_raw = deps.energia.ejecutar(datos, sizing_raw, strings_raw)
    nec_raw = deps.nec.ejecutar(datos, sizing_raw, strings_raw)
    finanzas_raw = deps.finanzas.ejecutar(datos, sizing_raw, energia_raw)

    # 🔹 Conversión a contratos fuertes internos
    sizing = ResultadoSizing(**sizing_raw)
    strings = ResultadoStrings(**strings_raw)
    nec = ResultadoNEC(**nec_raw)
    financiero = ResultadoFinanciero(**finanzas_raw)

    resultado = ResultadoProyecto(
        sizing=sizing,
        strings=strings,
        nec=nec,
        financiero=financiero,
    )

    # 🔹 ADAPTADOR HACIA UI / REPORTES (dict plano)
    return asdict(resultado)
