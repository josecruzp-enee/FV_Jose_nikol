from __future__ import annotations

"""
CONTRATO DEL DOMINIO ENERGÍA — FV Engine
========================================

Este módulo define la SALIDA OFICIAL del motor energético FV.

Regla arquitectónica
--------------------

El dominio energía NO define el sistema FV.
El sistema FV ya está completamente definido en:

    electrical.paneles → ResultadoPaneles

Por lo tanto:

    ✔ energía CONSUME ResultadoPaneles
    ❌ energía NO reconstruye parámetros eléctricos

Responsabilidad del dominio energía
-----------------------------------

Calcular la producción energética del sistema a partir de:

    • el generador FV (ResultadoPaneles)
    • clima horario (8760)
    • orientación
    • pérdidas
    • comportamiento del inversor

Modelo soportado
----------------

    ✔ Simulación física horaria (8760)

Este módulo NO contiene lógica de cálculo.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

# 👉 Fuente única del generador FV
from electrical.paneles.resultado_paneles import ResultadoPaneles


# ==========================================================
# (TEMPORAL) TIPO DE CLIMA
# ==========================================================

ResultadoClima = object


# ==========================================================
# ESTADO HORARIO (BASE DEL MODELO 8760)
# ==========================================================

@dataclass(frozen=True)
class EstadoEnergiaHora:
    """
    Estado energético del sistema en una hora específica.

    Representa el resultado físico del sistema FV en una
    condición climática dada.
    """

    poa_wm2: float
    temp_amb_c: float
    temp_celda_c: float

    p_dc_w: float
    p_ac_w: float

    energia_dc_wh: float
    energia_ac_wh: float


# ==========================================================
# ENTRADA DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaInput:
    """
    Entrada del motor energético FV (modelo 8760).
    """

    # ------------------------------------------------------
    # GENERADOR FV (FUENTE PRINCIPAL)
    # ------------------------------------------------------

    paneles: ResultadoPaneles

    # ------------------------------------------------------
    # INVERSOR
    # ------------------------------------------------------

    pac_nominal_kw: float
    eficiencia_inversor: float = 0.97
    permitir_clipping: bool = True

    # ------------------------------------------------------
    # GEOMETRÍA DEL SISTEMA
    # ------------------------------------------------------

    tilt_deg: float
    azimut_deg: float

    # ------------------------------------------------------
    # CLIMA
    # ------------------------------------------------------

    clima: ResultadoClima

    # ------------------------------------------------------
    # PÉRDIDAS
    # ------------------------------------------------------

    perdidas_dc_pct: float = 0.0
    perdidas_ac_pct: float = 0.0
    sombras_pct: float = 0.0

    # ======================================================
    # VALIDACIÓN DEL CONTRATO
    # ======================================================

    def validar(self) -> List[str]:

        errores: List[str] = []

        # -------------------------------
        # PANELes (CRÍTICO)
        # -------------------------------

        if self.paneles is None:
            errores.append("ResultadoPaneles requerido")

        elif not self.paneles.ok:
            errores.append("ResultadoPaneles no válido")

        elif not self.paneles.strings:
            errores.append("No hay strings definidos")

        # -------------------------------
        # POTENCIA
        # -------------------------------

        if self.pac_nominal_kw <= 0:
            errores.append("pac_nominal_kw debe ser > 0")

        # -------------------------------
        # GEOMETRÍA
        # -------------------------------

        if self.tilt_deg is None:
            errores.append("tilt_deg requerido")

        if self.azimut_deg is None:
            errores.append("azimut_deg requerido")

        # -------------------------------
        # CLIMA
        # -------------------------------

        if self.clima is None:
            errores.append("clima requerido (8760)")

        return errores


# ==========================================================
# RESULTADO DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado final del motor energético.

    Representa la producción completa del sistema FV.
    """

    # ------------------------------------------------------
    # ESTADO
    # ------------------------------------------------------

    ok: bool
    errores: List[str]

    # ------------------------------------------------------
    # POTENCIA
    # ------------------------------------------------------

    pdc_instalada_kw: float
    pac_nominal_kw: float
    dc_ac_ratio: float

    # ------------------------------------------------------
    # ENERGÍA HORARIA (8760)
    # ------------------------------------------------------

    energia_horaria: List[EstadoEnergiaHora]

    # ------------------------------------------------------
    # ENERGÍA MENSUAL
    # ------------------------------------------------------

    energia_bruta_12m: List[float]
    energia_perdidas_12m: List[float]
    energia_despues_perdidas_12m: List[float]
    energia_clipping_12m: List[float]
    energia_util_12m: List[float]

    # ------------------------------------------------------
    # ENERGÍA ANUAL
    # ------------------------------------------------------

    energia_bruta_anual: float
    energia_perdidas_anual: float
    energia_despues_perdidas_anual: float
    energia_clipping_anual: float
    energia_util_anual: float

    # ------------------------------------------------------
    # METADATA
    # ------------------------------------------------------

    meta: Dict[str, object] = field(default_factory=dict)


# ==========================================================
# SALIDA DEL DOMINIO
# ==========================================================

"""
Este módulo produce un único objeto:

EnergiaResultado


Estructura:

EnergiaResultado
    ├─ pdc_instalada_kw
    ├─ pac_nominal_kw
    ├─ dc_ac_ratio
    │
    ├─ energia_horaria: List[EstadoEnergiaHora]
    │      ├─ poa_wm2
    │      ├─ temp_amb_c
    │      ├─ temp_celda_c
    │      ├─ p_dc_w
    │      ├─ p_ac_w
    │      ├─ energia_dc_wh
    │      └─ energia_ac_wh
    │
    ├─ energia_bruta_12m
    ├─ energia_perdidas_12m
    ├─ energia_despues_perdidas_12m
    ├─ energia_clipping_12m
    ├─ energia_util_12m
    │
    ├─ energia_bruta_anual
    ├─ energia_perdidas_anual
    ├─ energia_despues_perdidas_anual
    ├─ energia_clipping_anual
    ├─ energia_util_anual
    │
    ├─ errores
    └─ meta
"""
