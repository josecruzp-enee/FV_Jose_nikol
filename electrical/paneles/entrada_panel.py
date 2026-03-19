from __future__ import annotations

"""
CONTRATO DE ENTRADA — DOMINIO PANELES (FV ENGINE)
================================================

Este módulo define la estructura de datos que INGRESA al dominio paneles.

----------------------------------------------------------
PROPÓSITO
----------------------------------------------------------

Centralizar y tipar todas las variables necesarias para:

    dimensionado de paneles
    cálculo de strings
    configuración del generador FV DC

Este contrato garantiza:

    - Consistencia de datos
    - Tipado fuerte
    - Desacoplamiento entre dominios

----------------------------------------------------------
ALCANCE DEL DOMINIO PANELES
----------------------------------------------------------

Este dominio SOLO se encarga de:

    - Dimensionar cantidad de paneles
    - Configurar strings (serie/paralelo)
    - Calcular parámetros eléctricos DC

NO incluye:

    - Energía (8760)
    - Irradiancia / clima
    - HSP / PR
    - Consumo del usuario
    - Pérdidas AC
    - Inversores AC

----------------------------------------------------------
ORIGEN DE LOS DATOS
----------------------------------------------------------

Este objeto es construido por:

    core.aplicacion (orquestador principal)

Y consumido por:

    electrical.paneles.orquestador_paneles

----------------------------------------------------------
ESTRUCTURA DE ENTRADA
----------------------------------------------------------
"""

from dataclasses import dataclass
from typing import Optional


# =========================================================
# ENTRADA DEL DOMINIO PANELES
# =========================================================

@dataclass(frozen=True)
class EntradaPaneles:
    """
    Representa TODOS los datos necesarios para ejecutar
    el dominio paneles.

    Este objeto es inmutable y debe estar completamente
    definido antes de entrar al dominio.
    """

    # -----------------------------------------------------
    # ESPECIFICACIÓN DEL MÓDULO FV
    # -----------------------------------------------------

    panel: any
    """
    Objeto PanelSpec.

    Contiene:
        - pmax_w
        - vmp_v
        - voc_v
        - imp_a
        - isc_a
        - coeficientes térmicos

    Fuente:
        catálogo de paneles (data / YAML)
    """

    # -----------------------------------------------------
    # ESPECIFICACIÓN DEL INVERSOR
    # -----------------------------------------------------

    inversor: any
    """
    Objeto InversorSpec.

    Contiene:
        - rango MPPT
        - número de MPPT
        - corriente máxima por MPPT
        - potencia nominal AC

    Fuente:
        catálogo de inversores
    """

    # -----------------------------------------------------
    # CONFIGURACIÓN DEL SISTEMA
    # -----------------------------------------------------

    n_paneles_total: Optional[int]
    """
    Número total de paneles (modo manual).

    Si se define:
        → se ignora pdc_kw_objetivo

    Si es None:
        → se usa modo automático
    """

    n_inversores: Optional[int]
    """
    Número de inversores en el sistema.

    Default implícito:
        1 si no se especifica
    """

    # -----------------------------------------------------
    # CONDICIONES TÉRMICAS
    # -----------------------------------------------------

    t_min_c: float
    """
    Temperatura mínima del sitio (°C).

    Usada para:
        cálculo de Voc en frío (condición crítica)
    """

    t_oper_c: float
    """
    Temperatura operativa típica (°C).

    Usada para:
        cálculo de Vmp real del sistema
    """

    # -----------------------------------------------------
    # CONFIGURACIÓN FÍSICA
    # -----------------------------------------------------

    dos_aguas: bool
    """
    Indica si el sistema está distribuido en dos orientaciones.

    True:
        distribución por MPPT separada

    False:
        sistema uniforme
    """

    # -----------------------------------------------------
    # OBJETIVO DE DISEÑO
    # -----------------------------------------------------

    objetivo_dc_ac: Optional[float]
    """
    Relación DC/AC objetivo.

    Ejemplo:
        1.2 → sobredimensionamiento DC

    Usado en:
        optimización de strings
    """

    pdc_kw_objetivo: Optional[float]
    """
    Potencia DC objetivo (kW).

    Usado en modo automático:

        demanda → cobertura → potencia requerida

    Si se define:
        se calcula n_paneles automáticamente
    """


# =========================================================
# RELACIÓN CON LA SALIDA DEL DOMINIO
# =========================================================

"""
FLUJO COMPLETO DEL DOMINIO PANELES
=================================

EntradaPaneles
    ↓
dimensionado_paneles
    ↓
PanelSizingResultado
    ↓
calculo_de_strings
    ↓
configuración MPPT
    ↓
ResultadoPaneles (SALIDA)

----------------------------------------------------------

SALIDA DEL DOMINIO:

    electrical.paneles.resultado_paneles.ResultadoPaneles

----------------------------------------------------------

REGLA DE FRONTERA:

EntradaPaneles  → SOLO ENTRADA
ResultadoPaneles → SOLO SALIDA

Nunca se mezclan.
Nunca se redefinen.
"""
