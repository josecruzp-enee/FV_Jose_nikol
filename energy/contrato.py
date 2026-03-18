from __future__ import annotations

"""
CONTRATO DEL DOMINIO ENERGÍA — FV Engine
========================================

Este módulo define las estructuras formales del dominio energía.

IMPORTANTE
----------

El dominio energía NO define el sistema FV.
El sistema FV es responsabilidad del dominio:

    electrical.paneles

Sin embargo, en la implementación actual:

    ✔ energía recibe paneles como dict estructurado
    ✔ energía valida fuertemente ese dict
    ❌ energía NO reconstruye el sistema

Esto es una adaptación controlada (no es solución final).

Responsabilidad del dominio energía
-----------------------------------

Calcular la producción energética del sistema a partir de:

    • generador FV (paneles)
    • clima horario (8760)
    • geometría
    • pérdidas
    • inversor

Modelo soportado
----------------

    ✔ Simulación física horaria (8760)

Este módulo NO contiene lógica de cálculo.
"""


# ==========================================================
# IMPORTS
# ==========================================================

from dataclasses import dataclass, field
from typing import List, Dict, Any


# ==========================================================
# (TEMPORAL) TIPO DE CLIMA
# ==========================================================

# ⚠️ Reemplazar por contrato real cuando exista
ResultadoClima = object


# ==========================================================
# ESTADO HORARIO (BASE DEL MODELO 8760)
# ==========================================================

@dataclass(frozen=True)
class EstadoEnergiaHora:
    """
    Estado energético en una hora específica.

    Representa el resultado físico del sistema FV bajo
    condiciones climáticas puntuales.
    """

    # Irradiancia en plano del arreglo
    poa_wm2: float

    # Temperaturas
    temp_amb_c: float
    temp_celda_c: float

    # Potencias instantáneas
    p_dc_w: float
    p_ac_w: float

    # Energía generada en la hora
    energia_dc_wh: float
    energia_ac_wh: float


# ==========================================================
# ENTRADA DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaInput:
    """
    Entrada del motor energético FV.

    Representa todos los datos necesarios para ejecutar
    la simulación física 8760.
    """

    # ------------------------------------------------------
    # GENERADOR FV
    # ------------------------------------------------------
    # ⚠️ Actualmente se recibe como dict estructurado
    # proveniente de electrical.paneles
    paneles: Dict[str, Any]

    # ------------------------------------------------------
    # INVERSOR
    # ------------------------------------------------------
    pac_nominal_kw: float

    # ------------------------------------------------------
    # GEOMETRÍA
    # ------------------------------------------------------
    tilt_deg: float
    azimut_deg: float

    # ------------------------------------------------------
    # CLIMA
    # ------------------------------------------------------
    clima: Any

    # ------------------------------------------------------
    # PARÁMETROS DEL SISTEMA
    # ------------------------------------------------------
    eficiencia_inversor: float = 0.97
    permitir_clipping: bool = True

    perdidas_dc_pct: float = 0.0
    perdidas_ac_pct: float = 0.0
    sombras_pct: float = 0.0

    # ======================================================
    # VALIDACIÓN DEL CONTRATO
    # ======================================================

    def validar(self) -> List[str]:
        """
        Valida consistencia de la entrada.

        Regla:
            Si algo falta → se reporta error
        """

        errores: List[str] = []

        # -------------------------------
        # PANELes (CRÍTICO)
        # -------------------------------
        if not isinstance(self.paneles, dict):
            errores.append("paneles debe ser dict")

        else:

            if not self.paneles.get("ok", False):
                errores.append("paneles no válido")

            if "strings" not in self.paneles:
                errores.append("paneles sin strings")

            if "n_strings_total" not in self.paneles:
                errores.append("paneles sin n_strings_total")

        # -------------------------------
        # POTENCIA
        # -------------------------------
        if self.pac_nominal_kw <= 0:
            errores.append("pac_nominal_kw inválido")

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
            errores.append("clima requerido")

        return errores


# ==========================================================
# RESULTADO DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado final del motor energético.

    Contiene toda la producción del sistema FV:
    horaria, mensual y anual.
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
