from __future__ import annotations

"""
ORQUESTADOR DEL ESTUDIO FV — FV Engine

FRONTERA DEL MÓDULO
-------------------
Este archivo representa la frontera entre la UI y el motor interno del sistema.

Responsabilidad:
    Orquestar los dominios del motor FV siguiendo el flujo maestro del software.

Flujo maestro:
    1) Dimensionamiento FV (Sizing)
    2) Paneles / Strings
    3) Ingeniería eléctrica
    4) Producción energética
    5) Evaluación financiera

Reglas de arquitectura:
    - La UI SOLO llama a este módulo.
    - Este módulo SOLO coordina dominios.
    - Los dominios realizan los cálculos.
    - Este módulo NO realiza cálculos físicos.
"""

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
# DEPENDENCIAS (PUERTOS DEL SISTEMA)
# ==========================================================

@dataclass
class DependenciasEstudio:
    """
    Contenedor de dependencias del motor FV.

    Cada puerto representa un dominio del sistema.
    """
    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    nec: PuertoNEC
    finanzas: PuertoFinanzas


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================

def ejecutar_estudio(
    datos: Any,
    deps: DependenciasEstudio,
):
    """
    Ejecuta el flujo completo de análisis del sistema FV.

    ENTRADA
    -------
    datos :
        Datos del proyecto FV (dict o objeto DatosProyecto)

    deps :
        Dependencias del sistema (implementaciones de puertos)

    SALIDA
    ------
    dict

        Resultado completo del estudio FV serializable para UI.

    NOTA
    ----
    Esta función es la frontera hacia la UI.
    """

    # ------------------------------------------------------
    # 1. Dimensionamiento FV
    # ------------------------------------------------------

    sizing = deps.sizing.ejecutar(datos)

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
    # Consolidación de resultados
    # ------------------------------------------------------

    resultado = ResultadoProyecto(
        sizing=sizing,
        strings=strings,
        energia=energia,
        nec=nec,
        financiero=financiero,
    )

    # ------------------------------------------------------
    # FRONTERA HACIA UI
    # ------------------------------------------------------

    return asdict(resultado)


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# ejecutar_estudio()
#
# Entradas:
#   datos
#   deps
#
# Salida:
#   dict con el resultado completo del estudio FV
#
# Consumido por:
#   UI (Streamlit / API / CLI)
#
# ==========================================================
