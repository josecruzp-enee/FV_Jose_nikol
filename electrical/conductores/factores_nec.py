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

from dataclasses import dataclass


# ==========================================================
# RESULTADO TIPADO
# ==========================================================

@dataclass(frozen=True)
class AmpacidadResultado:
    """
    Resultado del ajuste de ampacidad según NEC.
    """

    ampacidad_ajustada: float
    factor_temperatura: float
    factor_ccc: float


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
    Calcula el factor de corrección por temperatura ambiente.

    ----------------------------------------------------------
    ENTRADA

    t_amb_c:
        temperatura ambiente [°C]

    columna:
        tipo de conductor:
            "75C" → terminal típico
            "90C" → THWN-2 / PV Wire

    ----------------------------------------------------------
    SALIDA

    factor:
        multiplicador de ampacidad (0.71 – 1.00)

    ----------------------------------------------------------
    NOTA

    Tabla simplificada (no interpolada).
    """

    try:
        t = float(t_amb_c)
    except Exception:
        raise ValueError("t_amb_c inválido")

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
# FACTOR AGRUPAMIENTO (CCC)
# ==========================================================

def factor_agrupamiento_ccc(
    ccc: int
) -> float:
    """
    Calcula el factor por número de conductores portadores.

    ----------------------------------------------------------
    ENTRADA

    ccc:
        número de conductores portadores de corriente

    ----------------------------------------------------------
    SALIDA

    factor:
        multiplicador de ampacidad (0.50 – 1.00)
    """

    try:
        n = int(ccc)
    except Exception:
        raise ValueError("ccc inválido")

    if n <= 3:
        return 1.00
    if n <= 6:
        return 0.80
    if n <= 9:
        return 0.70
    return 0.50


# ==========================================================
# AMPACIDAD AJUSTADA (FUNCIÓN PRINCIPAL)
# ==========================================================

def ampacidad_ajustada_nec(
    ampacidad_base: float,
    t_amb_c: float,
    ccc: int,
    aplicar: bool = True,
    *,
    columna: str = "75C",
) -> AmpacidadResultado:
    """
    Aplica factores NEC a la ampacidad base.

    ----------------------------------------------------------
    ENTRADAS

    ampacidad_base:
        ampacidad nominal del conductor [A]

    t_amb_c:
        temperatura ambiente [°C]

    ccc:
        conductores portadores de corriente

    aplicar:
        True  → aplicar factores NEC
        False → devolver ampacidad base

    columna:
        "75C" o "90C"

    ----------------------------------------------------------
    PROCESO

    ampacidad_ajustada =
        ampacidad_base × f_temp × f_ccc

    ----------------------------------------------------------
    SALIDA

    AmpacidadResultado:

        ampacidad_ajustada
        factor_temperatura
        factor_ccc
    """

    try:
        amp_base = float(ampacidad_base)
    except Exception:
        raise ValueError("ampacidad_base inválida")

    if amp_base <= 0:
        return AmpacidadResultado(0.0, 1.0, 1.0)

    if not aplicar:
        return AmpacidadResultado(amp_base, 1.0, 1.0)

    f_temp = factor_temperatura_nec(t_amb_c, columna=columna)
    f_ccc = factor_agrupamiento_ccc(ccc)

    amp_adj = amp_base * f_temp * f_ccc

    return AmpacidadResultado(
        ampacidad_ajustada=float(amp_adj),
        factor_temperatura=float(f_temp),
        factor_ccc=float(f_ccc),
    )


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# FUNCIÓN PRINCIPAL:
# ----------------------------------------------------------
# ampacidad_ajustada_nec(...)
#
#
# ----------------------------------------------------------
# ENTRADA
# ----------------------------------------------------------
#
# ampacidad_base : float
#     → ampacidad nominal del conductor
#
# t_amb_c : float
#     → temperatura ambiente
#
# ccc : int
#     → conductores portadores
#
# aplicar : bool
#     → aplicar o no factores NEC
#
# columna : str
#     → tipo de conductor (75C / 90C)
#
#
# ----------------------------------------------------------
# PROCESO
# ----------------------------------------------------------
#
# 1. Calcula factor por temperatura
# 2. Calcula factor por agrupamiento
# 3. Ajusta ampacidad
#
#
# ----------------------------------------------------------
# VARIABLES CLAVE
# ----------------------------------------------------------
#
# ampacidad_ajustada
#     → valor final para validación
#
# factor_temperatura
#     → impacto térmico
#
# factor_ccc
#     → impacto por agrupamiento
#
#
# ----------------------------------------------------------
# SALIDA
# ----------------------------------------------------------
#
# AmpacidadResultado:
#
#   ampacidad_ajustada
#   factor_temperatura
#   factor_ccc
#
#
# ----------------------------------------------------------
# USO EN FV ENGINE
# ----------------------------------------------------------
#
# Este módulo es consumido por:
#
#   electrical.conductores.tramo_conductor
#
# Para validar:
#
#   i_diseno <= ampacidad_ajustada
#
#
# ----------------------------------------------------------
# UBICACIÓN EN FLUJO
# ----------------------------------------------------------
#
# Corrientes
#       ↓
# conductores (tramo_conductor)
#       ↓
# FACTORES NEC (este módulo)
#       ↓
# validación final
#
#
# ----------------------------------------------------------
# PRINCIPIO
# ----------------------------------------------------------
#
# Este módulo NO selecciona conductores.
#
# SOLO responde:
#
#   "¿Este conductor cumple ampacidad?"
#
# ==========================================================
