from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.dominio.contrato import ResultadoProyecto
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


def ejecutar_estudio(
    datos: Any,
    deps: DependenciasEstudio,
) -> ResultadoProyecto:

    # ------------------------------------------------------
    # 1. SIZING
    # ------------------------------------------------------

    sizing = deps.sizing.ejecutar(datos)

    if not sizing.ok:
        return ResultadoProyecto(
            sizing=sizing,
            strings=None,
            energia=None,
            nec=None,
            financiero=None,
        )

    # ------------------------------------------------------
    # 2. PANELES
    # ------------------------------------------------------

    paneles = deps.paneles.ejecutar(
        datos,
        sizing,
    )

    # ------------------------------------------------------
    # 3. NEC
    # ------------------------------------------------------

    nec = deps.nec.ejecutar(
        datos,
        sizing,
        paneles,
    )

    # ------------------------------------------------------
    # 4. ENERGÍA
    # ------------------------------------------------------

    energia = deps.energia.ejecutar(
        datos,
        sizing,
        paneles,
    )

    # ------------------------------------------------------
    # 5. FINANZAS
    # ------------------------------------------------------

    financiero = deps.finanzas.ejecutar(
        datos,
        sizing,
        energia,
    )

    # ------------------------------------------------------
    # RESULTADO FINAL
    # ------------------------------------------------------

    return ResultadoProyecto(
        sizing=sizing,
        strings=paneles,
        energia=energia,
        nec=nec,
        financiero=financiero,
    )
