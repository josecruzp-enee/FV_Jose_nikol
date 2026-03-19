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

    # -----------------------------------------------------
    # ESPECIFICACIÓN DEL MÓDULO FV
    # -----------------------------------------------------

    panel: any

    # -----------------------------------------------------
    # ESPECIFICACIÓN DEL INVERSOR
    # -----------------------------------------------------

    inversor: any

    # -----------------------------------------------------
    # CONFIGURACIÓN DEL SISTEMA
    # -----------------------------------------------------

    n_paneles_total: Optional[int] = None
    n_inversores: Optional[int] = None

    # -----------------------------------------------------
    # CONDICIONES TÉRMICAS
    # -----------------------------------------------------

    t_min_c: float = 25.0
    t_oper_c: float = 55.0

    # -----------------------------------------------------
    # CONFIGURACIÓN FÍSICA
    # -----------------------------------------------------

    dos_aguas: bool = False

    # -----------------------------------------------------
    # OBJETIVO DE DISEÑO
    # -----------------------------------------------------

    objetivo_dc_ac: Optional[float] = None
    pdc_kw_objetivo: Optional[float] = None
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
