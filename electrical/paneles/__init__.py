# electrical/paneles/__init__.py
from __future__ import annotations

from .dimensionado_paneles import calcular_panel_sizing
from .calculo_de_strings import calcular_strings_fv, InversorSpec, PanelSpec
from .orquestador_paneles import (
    a_lineas_strings,
    ejecutar_calculo_strings,
    ejecutar_paneles_por_demanda,
)
from .resumen_strings import resumen_strings
from .validacion_strings import (
    validar_inversor,
    validar_panel,
    validar_parametros_generales,
)

__all__ = [
    "ejecutar_paneles_por_demanda",
    "calcular_panel_sizing",
    "calcular_strings_fv",
    "ejecutar_calculo_strings",
    "a_lineas_strings",
    "resumen_strings",
    "PanelSpec",
    "InversorSpec",
    "validar_panel",
    "validar_inversor",
    "validar_parametros_generales",
]
