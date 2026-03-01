from dataclasses import dataclass
from typing import Any, Dict

from .puertos import (
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


def ejecutar_estudio(datos: Any, deps: DependenciasEstudio) -> Dict[str, Any]:
    sizing = deps.sizing.ejecutar(datos)
    strings = deps.paneles.ejecutar(datos, sizing)
    energia = deps.energia.ejecutar(datos, sizing, strings)
    nec = deps.nec.ejecutar(datos, sizing, strings)
    finanzas = deps.finanzas.ejecutar(datos, sizing, energia)

    return {
        "sizing": sizing,
        "strings": strings,
        "energia": energia,
        "nec": nec,
        "financiero": finanzas,
    }
