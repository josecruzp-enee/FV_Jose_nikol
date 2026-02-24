"""
Paneles FV — API pública del dominio paneles.

Mantiene compatibilidad con imports antiguos mientras se completa el refactor.
"""

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
import sys

sys.modules[__name__ + ".sizing_panel"] = sys.modules[__name__ + ".dimensionado_paneles"]
sys.modules[__name__ + ".validador_strings"] = sys.modules[__name__ + ".validacion_strings"]
sys.modules[__name__ + ".strings_auto"] = sys.modules[__name__ + ".calculo_de_strings"]
