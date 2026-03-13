from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO PANELES

## FRONTERA DEL DOMINIO

Este módulo coordina el cálculo del generador fotovoltaico.

Flujo del dominio:

EntradaPaneles
↓
validaciones
↓
dimensionado de paneles
↓
cálculo de strings
↓
resultado del dominio

Este módulo NO implementa cálculos físicos complejos.
Solo coordina los motores del dominio.
"""

from typing import Dict, List

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec
from .calculo_de_strings import calcular_strings_fv
from .dimensionado_paneles import dimensionar_paneles
from .entrada_panel import EntradaPaneles
from .validacion_strings import (
validar_panel,
validar_inversor,
validar_parametros_generales,
)

# ==========================================================

# ORQUESTADOR

# ==========================================================

def ejecutar_paneles(
entrada: EntradaPaneles
) -> Dict:

```
import streamlit as st

errores: List[str] = []
warnings: List[str] = []

panel: PanelSpec = entrada.panel
inversor: InversorSpec = entrada.inversor

# ------------------------------------------------------
# VALIDACIONES
# ------------------------------------------------------

e, w = validar_panel(panel)
errores += e
warnings += w

e, w = validar_inversor(inversor)
errores += e
warnings += w

e, w = validar_parametros_generales(
    entrada.n_paneles_total,
    entrada.t_min_c,
    entrada.t_oper_c,
)

errores += e
warnings += w

if errores:
    return {
        "ok": False,
        "errores": errores,
        "warnings": warnings,
    }

# ------------------------------------------------------
# DIMENSIONADO DE PANELES
# ------------------------------------------------------

dim = dimensionar_paneles(entrada)

if not dim.ok:
    return {
        "ok": False,
        "errores": dim.errores,
        "warnings": warnings,
    }

n_paneles_total = dim.n_paneles

# DEBUG DIMENSIONADO
st.write("DEBUG DIMENSIONADO PANELES")
st.write({
    "entrada_paneles": entrada.n_paneles_total,
    "paneles_dimensionados": dim.n_paneles,
    "pdc_kw": dim.pdc_kw
})

# ------------------------------------------------------
# CÁLCULO DE STRINGS
# ------------------------------------------------------

n_inversores = int(entrada.n_inversores or 1)

st.write("DEBUG ANTES DE STRINGS")
st.write({
    "n_paneles_total_enviado": n_paneles_total,
    "n_inversores": n_inversores,
    "mppt_por_inversor": inversor.n_mppt
})

resultado = calcular_strings_fv(
    n_paneles_total=n_paneles_total,
    panel=panel,
    inversor=inversor,
    n_inversores=n_inversores,
    t_min_c=float(entrada.t_min_c),
    dos_aguas=bool(entrada.dos_aguas),
    objetivo_dc_ac=entrada.objetivo_dc_ac,
    pdc_kw_objetivo=entrada.pdc_kw_objetivo,
    t_oper_c=entrada.t_oper_c,
)

# DEBUG RESULTADO
st.write("DEBUG RESULTADO STRINGS")
st.write("numero strings:", len(resultado.get("strings", [])))

resultado.setdefault("ok", False)
resultado.setdefault("errores", [])
resultado.setdefault("warnings", [])

resultado["warnings"] = warnings + resultado["warnings"]

# ------------------------------------------------------
# META DEL DIMENSIONADO
# ------------------------------------------------------

resultado.setdefault("meta", {})

resultado["meta"]["n_paneles_total"] = n_paneles_total
resultado["meta"]["pdc_kw"] = dim.pdc_kw

return resultado
```

# ==========================================================

# SALIDAS DEL ARCHIVO

# ==========================================================

#

# ejecutar_paneles(entrada: EntradaPaneles)

#

# devuelve:

#

# ok : bool

# errores : list[str]

# warnings : list[str]

#

# strings : list

#

# recomendacion:

# n_series

# n_strings_total

# vmp_string_v

# voc_string_v

# imp_array_a

# isc_array_total_a

#

# bounds:

# n_min

# n_max

#

# meta:

# n_paneles_total

# pdc_kw

#

# Consumido por:

# core

#

# ==========================================================
