from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from core.dominio.contrato import ResultadoProyecto

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
    PuertoFinanzas,
)


# ==========================================================
# DEPENDENCIAS
# ==========================================================

@dataclass
class DependenciasEstudio:

    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    nec: PuertoNEC
    finanzas: PuertoFinanzas


# ==========================================================
# ORQUESTADOR
# ==========================================================

def ejecutar_estudio(
    datos: Any,
    deps: DependenciasEstudio,
):
   

    # ------------------------------------------------------
    # 1. Dimensionamiento FV
    # ------------------------------------------------------

    sizing = deps.sizing.ejecutar(datos)

    if getattr(sizing, "ok", True) is False:
        return asdict(ResultadoProyecto(
            sizing=sizing,
            strings=None,
            energia=None,
            nec=None,
            financiero=None,
        ))

    # ------------------------------------------------------
    # 2. Paneles / Strings
    # ------------------------------------------------------

    strings = deps.paneles.ejecutar(
        datos,
        sizing,
    )

    # ------------------------------------------------------
    # 3. Ingeniería eléctrica
    # ------------------------------------------------------

    nec = deps.nec.ejecutar(
        datos,
        sizing,
        strings,
    )

    # ------------------------------------------------------
    # 4. Producción energética
    # ------------------------------------------------------

    energia = deps.energia.ejecutar(
        datos,
        sizing,
        strings,
    )

    # ------------------------------------------------------
    # 5. Evaluación financiera
    # ------------------------------------------------------

    financiero = deps.finanzas.ejecutar(
        datos,
        sizing,
        energia,
    )

    # ------------------------------------------------------
    # Consolidación final
    # ------------------------------------------------------

    resultado = ResultadoProyecto(
        sizing=sizing,
        strings=strings,
        energia=energia,
        nec=nec,
        financiero=financiero,
    )

    return resultado
