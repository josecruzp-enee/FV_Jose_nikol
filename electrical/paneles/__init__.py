# Paneles FV — API pública del dominio paneles: exports oficiales + compatibilidad temporal de imports legacy.
from __future__ import annotations

# ===============================
# EXPORTS OFICIALES (API PÚBLICA)
# ===============================
from .dimensionado_paneles import calcular_panel_sizing
from .calculo_de_strings import calcular_strings_fv, InversorSpec, PanelSpec
from .orquestador_paneles import a_lineas_strings, ejecutar_calculo_strings
from .resumen_strings import resumen_strings
from .validacion_strings import (
    InversorFV,
    PanelFV,
    validar_inversor,
    validar_panel,
    validar_parametros_generales,
)

__all__ = [
    # Dimensionado energético
    "calcular_panel_sizing",
    # Motor/orquestación de strings
    "calcular_strings_fv",
    "ejecutar_calculo_strings",
    "a_lineas_strings",
    "resumen_strings",
    # Contratos internos
    "PanelSpec",
    "InversorSpec",
    # Validación pura (sin motor)
    "PanelFV",
    "InversorFV",
    "validar_panel",
    "validar_inversor",
    "validar_parametros_generales",
]

