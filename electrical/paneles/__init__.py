from .calculo_de_strings import (
    calcular_strings_fv,
    calcular_strings_auto,
    PanelSpec,
    InversorSpec,
)
from .orquestador_paneles import ejecutar_calculo_strings, a_lineas_strings
__all__ = ["calcular_strings_fv"]

"""
Paneles FV — capa pública del módulo.

Este archivo mantiene compatibilidad con nombres antiguos
mientras se completa el refactor.
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
from .validacion_strings import PanelFV, InversorFV, validar_string


# ===============================
# PARCHE COMPATIBILIDAD (IMPORTS VIEJOS)
# ===============================
# Permite que código antiguo siga funcionando:
# from electrical.paneles.sizing_panel import ...
# from electrical.paneles.validador_strings import ...

import sys

sys.modules[__name__ + ".sizing_panel"] = sys.modules[
    __name__ + ".dimensionado_paneles"
]

sys.modules[__name__ + ".validador_strings"] = sys.modules[
    __name__ + ".validacion_strings"
]

sys.modules[__name__ + ".strings_auto"] = sys.modules[
    __name__ + ".calculo_de_strings"
]
