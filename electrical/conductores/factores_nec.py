from __future__ import annotations

"""
FACTORES DE CORRECCIÓN NEC — FV ENGINE
=====================================

🔷 PROPÓSITO
----------------------------------------------------------
Aplicar factores normativos NEC para ajustar la ampacidad
de conductores eléctricos.

Este módulo calcula:

    ✔ Factor por temperatura ambiente
    ✔ Factor por agrupamiento (CCC)
    ✔ Ampacidad ajustada

----------------------------------------------------------
🔷 ALCANCE
----------------------------------------------------------

Este módulo NO realiza:

    ✘ Selección de calibre
    ✘ Cálculo de caída de voltaje
    ✘ Lectura de tablas AWG

----------------------------------------------------------
🔷 NORMATIVA
----------------------------------------------------------

    NEC 310.15(B)(1) → Corrección por temperatura
    NEC 310.15(C)(1) → Ajuste por conductores (CCC)

----------------------------------------------------------
🔷 FILOSOFÍA
----------------------------------------------------------

Este módulo NO decide nada.

Solo aplica factores:
    entrada → ampacidad base
    salida  → ampacidad corregida
"""

from typing import Tuple


# ==========================================================
# REFERENCIAS NORMATIVAS
# ==========================================================

NEC_REFERENCIAS = [
    "NEC 310.15(B)(1) - Ambient Temperature Correction",
    "NEC 310.15(C)(1) - Adjustment Factors for Current-Carrying Conductors",
]


# ==========================================================
# FACTOR TEMPERATURA
# ==========================================================

def factor_temperatura_nec(
    t_amb_c: float,
    columna: str = "75C",
) -> float:
    """
    🔷 ENTRADA

    t_amb_c:
        → temperatura ambiente [°C]

    columna:
        → "75C" (terminal típico)
        → "90C" (THWN-2 / PV wire)

    🔷 SALIDA

    factor:
        → multiplicador de ampacidad (0.71 – 1.0)
    """

    try:
        t = float(t_amb_c)
    except Exception:
        t = 30.0

    col = str(columna).strip().upper()

    if col not in {"75C", "90C"}:
        col = "75C"

    # NEC simplificado por tramos

    if t <= 30:
        return 1.00
    if t <= 40:
        return 0.91
    if t <= 50:
        return 0.82
    return 0.71


# ==========================================================
# FACTOR CCC (AGRUPAMIENTO)
# ==========================================================

def factor_agrupamiento_ccc(
    ccc: int
) -> float:
    """
    🔷 ENTRADA

    ccc:
        → número de conductores portadores de corriente

    🔷 SALIDA

    factor:
        → multiplicador de ampacidad (0.5 – 1.0)
    """

    try:
        n = int(ccc)
    except Exception:
        n = 1

    if n <= 3:
        return 1.00
    if n <= 6:
        return 0.80
    if n <= 9:
        return 0.70
    return 0.50


# ==========================================================
# AMPACIDAD AJUSTADA
# ==========================================================

def ampacidad_ajustada_nec(
    ampacidad_base: float,
    t_amb_c: float,
    ccc: int,
    aplicar: bool = True,
    *,
    columna: str = "75C",
) -> Tuple[float, float, float]:
    """
    🔷 ENTRADAS

    ampacidad_base:
        → ampacidad nominal del conductor [A]

    t_amb_c:
        → temperatura ambiente [°C]

    ccc:
        → conductores portadores de corriente

    aplicar:
        → True → aplicar factores NEC
        → False → devolver ampacidad base

    columna:
        → "75C" o "90C"

    ----------------------------------------------------------

    🔷 PROCESO

    ampacidad_ajustada =
        ampacidad_base × f_temp × f_ccc

    ----------------------------------------------------------

    🔷 SALIDA (TUPLA)

    ampacidad_ajustada:
        → ampacidad final corregida

    factor_temperatura:
        → factor aplicado por temperatura

    factor_ccc:
        → factor aplicado por agrupamiento
    """

    try:
        amp_base = float(ampacidad_base)
    except Exception:
        amp_base = 0.0

    if amp_base <= 0.0:
        return 0.0, 1.0, 1.0

    if not bool(aplicar):
        return amp_base, 1.0, 1.0

    f_temp = factor_temperatura_nec(t_amb_c, columna=columna)
    f_ccc = factor_agrupamiento_ccc(ccc)

    amp_adj = amp_base * f_temp * f_ccc

    return float(amp_adj), float(f_temp), float(f_ccc)


# ==========================================================
# RESUMEN DE VARIABLES DE SALIDA
# ==========================================================

"""
SALIDA PRINCIPAL
================

ampacidad_ajustada_nec(...) devuelve:

    (ampacidad_ajustada, factor_temperatura, factor_ccc)

----------------------------------------------------------

1. ampacidad_ajustada
----------------------------------------------------------

    [A]

    Capacidad real del conductor después de aplicar:

        temperatura
        agrupamiento (CCC)

    👉 Esta es la que se usa para validar:

        i_diseno <= ampacidad_ajustada

----------------------------------------------------------

2. factor_temperatura
----------------------------------------------------------

    [adimensional]

    Factor aplicado por temperatura ambiente.

    Ejemplo:
        30°C → 1.00
        40°C → 0.91

----------------------------------------------------------

3. factor_ccc
----------------------------------------------------------

    [adimensional]

    Factor por número de conductores.

    Ejemplo:
        2 conductores → 1.00
        6 conductores → 0.80

----------------------------------------------------------

USO EN FV ENGINE
----------------------------------------------------------

Este módulo es consumido por:

    electrical.conductores.tramo_conductor

Para validar:

    ✔ ampacidad
    ✔ cumplimiento NEC

----------------------------------------------------------

REGLA CLAVE
----------------------------------------------------------

Este módulo NO selecciona calibre.

Solo responde:

    "¿Este conductor aguanta o no?"
"""
