"""
Paneles FV — API pública del dominio paneles.

Mantiene compatibilidad con imports antiguos mientras se completa el refactor.
"""

from __future__ import annotations

# ===============================
# NUEVOS NOMBRES (OFICIALES)
# ===============================
from .dimensionado_paneles import calcular_panel_sizing
from .calculo_de_strings import (
    calcular_strings_fv,
    calcular_strings_auto,
    PanelSpec,
    InversorSpec,
)
from .validacion_strings import (
    PanelFV,
    InversorFV,
    validar_string,
)
from .orquestador_paneles import (
    ejecutar_calculo_strings,
    a_lineas_strings,
)

__all__ = [
    "calcular_panel_sizing",
    "calcular_strings_fv",
    "calcular_strings_auto",
    "PanelSpec",
    "InversorSpec",
    "PanelFV",
    "InversorFV",
    "validar_string",
    "ejecutar_calculo_strings",
    "a_lineas_strings",
]

# ===============================
# PARCHE COMPATIBILIDAD (IMPORTS VIEJOS)
# ===============================
import importlib
import sys

# Asegurar módulos cargados
_mod_dimensionado = importlib.import_module(__name__ + ".dimensionado_paneles")
_mod_validacion = importlib.import_module(__name__ + ".validacion_strings")
_mod_calculo = importlib.import_module(__name__ + ".calculo_de_strings")

# Aliases para imports viejos (mantener mientras migra el código legacy)
sys.modules[__name__ + ".sizing_panel"] = _mod_dimensionado
sys.modules[__name__ + ".validador_strings"] = _mod_validacion
sys.modules[__name__ + ".strings_auto"] = _mod_calculo
