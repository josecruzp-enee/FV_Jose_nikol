from dataclasses import dataclass, asdict
from typing import Any

from core.dominio.contrato import (
    ResultadoProyecto,
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

    # 🔹 Ejecución directa (ya devuelven contratos fuertes)
    sizing = deps.sizing.ejecutar(datos)
    strings = deps.paneles.ejecutar(datos, sizing)
    energia = deps.energia.ejecutar(datos, sizing, strings)
    nec = deps.nec.ejecutar(datos, sizing, strings)
    financiero = deps.finanzas.ejecutar(datos, sizing, energia)

    resultado = ResultadoProyecto(
        sizing=sizing,
        strings=strings,
        nec=nec,
        financiero=financiero,
    )

    # 🔹 Frontera hacia UI
    return asdict(resultado)
