from dataclasses import dataclass, asdict
from typing import Any
from core.servicios.analisis_cobertura import analizar_cobertura
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

print("VERSIÓN ORQUESTADOR NUEVA ACTIVA")
@dataclass
class DependenciasEstudio:
    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    nec: PuertoNEC
    finanzas: PuertoFinanzas


def ejecutar_estudio(datos: Any, deps: DependenciasEstudio):

    sizing = deps.sizing.ejecutar(datos)
    strings = deps.paneles.ejecutar(datos, sizing)
    energia = deps.energia.ejecutar(datos, sizing, strings)
    nec = deps.nec.ejecutar(datos, sizing, strings)
    financiero = deps.finanzas.ejecutar(datos, sizing, energia)

    resultado = ResultadoProyecto(
        sizing=sizing,
        strings=strings,
        energia=energia,
        nec=nec,
        financiero=financiero,
    )
    #fontera a ui. 
    return asdict(resultado)
