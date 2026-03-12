from __future__ import annotations

"""
PUERTOS DEL SISTEMA — FV Engine

Este módulo define las interfaces que conectan el orquestador
del sistema con los distintos dominios del motor FV.

Los puertos representan CONTRATOS.

El orquestador solo conoce estos contratos.
Las implementaciones viven en los dominios:

    electrical.paneles
    electrical.ingenieria_electrica
    electrical.energia
    core.servicios.finanzas
"""

from typing import Protocol, Dict, Any


# ==========================================================
# PUERTO: SIZING
# ==========================================================

class PuertoSizing(Protocol):
    """
    Dimensionamiento del sistema FV.

    Entrada:
        datos del proyecto

    Salida:
        ResultadoSizing
    """

    def ejecutar(
        self,
        datos: Any,
    ) -> Dict[str, Any]: ...


# ==========================================================
# PUERTO: PANELES / STRINGS
# ==========================================================

class PuertoPaneles(Protocol):
    """
    Generación de strings FV.

    Entrada:
        datos del proyecto
        resultado de sizing

    Salida:
        resultado de strings
    """

    def ejecutar(
        self,
        datos: Any,
        sizing: Dict[str, Any],
    ) -> Dict[str, Any]: ...


# ==========================================================
# PUERTO: INGENIERÍA ELÉCTRICA
# ==========================================================

class PuertoNEC(Protocol):
    """
    Ingeniería eléctrica del sistema FV.

    Incluye:

        corrientes
        protecciones
        conductores
        canalización

    Entrada:
        datos
        sizing
        strings

    Salida:
        paquete eléctrico completo
    """

    def ejecutar(
        self,
        datos: Any,
        sizing: Dict[str, Any],
        strings: Dict[str, Any],
    ) -> Dict[str, Any]: ...


# ==========================================================
# PUERTO: PRODUCCIÓN ENERGÉTICA
# ==========================================================

class PuertoEnergia(Protocol):
    """
    Cálculo de producción energética del sistema FV.

    Entrada:
        datos
        sizing
        strings

    Salida:
        resultado energético
    """

    def ejecutar(
        self,
        datos: Any,
        sizing: Dict[str, Any],
        strings: Dict[str, Any],
    ) -> Dict[str, Any]: ...


# ==========================================================
# PUERTO: FINANZAS
# ==========================================================

class PuertoFinanzas(Protocol):
    """
    Evaluación financiera del proyecto FV.

    Entrada:
        datos
        sizing
        energía generada

    Salida:
        análisis financiero
    """

    def ejecutar(
        self,
        datos: Any,
        sizing: Dict[str, Any],
        energia: Dict[str, Any],
    ) -> Dict[str, Any]: ...


# ==========================================================
# RESUMEN DE PUERTOS
# ==========================================================
#
# PuertoSizing
# PuertoPaneles
# PuertoNEC
# PuertoEnergia
# PuertoFinanzas
#
# Consumidos por:
#   core.aplicacion.orquestador_estudio
#
# Implementados por:
#   dominios del motor FV
#
# ==========================================================
