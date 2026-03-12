"""
Modelo simplificado de orientación del generador FV.

Este módulo calcula el factor de orientación anual del sistema
fotovoltaico en función del azimut del generador.

El modelo utiliza una penalización coseno suavizada respecto
a la orientación óptima.

NO calcula:
- irradiancia
- pérdidas
- clipping
- producción energética
"""

from __future__ import annotations
import math


# ==========================================================
# UTILIDADES ANGULARES
# ==========================================================

def delta_azimut_deg(az_deg: float, ref_deg: float = 180.0) -> float:
    """
    Diferencia angular mínima entre azimut y referencia.

    Maneja continuidad circular (0–360°).
    """

    d = abs(float(az_deg) - float(ref_deg)) % 360.0
    return min(d, 360.0 - d)


# ==========================================================
# FACTOR ORIENTACION SIMPLE
# ==========================================================

def factor_orientacion(az_deg: float, hemisferio: str = "norte") -> float:
    """
    Factor anual simplificado por orientación.

    Parámetros
    ----------
    az_deg:
        Azimut del generador FV (°)

    hemisferio:
        "norte" o "sur"

    Retorna
    -------
    factor_orientacion : float
        Factor entre 0.35 y 1.0
    """

    ref = 0.0 if hemisferio.lower() == "sur" else 180.0
    delta = delta_azimut_deg(az_deg, ref)

    f = (1.0 + math.cos(math.radians(delta))) / 2.0

    return max(0.35, min(1.00, f))


# ==========================================================
# FACTOR ORIENTACION TOTAL
# ==========================================================

def factor_orientacion_total(
    tipo_superficie: str,
    azimut_deg: float,
    azimut_a_deg: float | None = None,
    azimut_b_deg: float | None = None,
    reparto_pct_a: float | None = None,
    hemisferio: str = "norte",
) -> float:
    """
    Calcula factor total considerando:

    - Superficie plana
    - Techo dos aguas (ponderado energético)
    """

    tipo = str(tipo_superficie or "plano").lower()

    # ------------------------------------------
    # Caso plano
    # ------------------------------------------

    if tipo != "dos_aguas":
        return factor_orientacion(azimut_deg, hemisferio=hemisferio)

    # ------------------------------------------
    # Fallback seguro
    # ------------------------------------------

    if azimut_a_deg is None or azimut_b_deg is None or reparto_pct_a is None:
        return factor_orientacion(azimut_deg, hemisferio=hemisferio)

    # ------------------------------------------
    # Cálculo ponderado
    # ------------------------------------------

    w_a = max(0.0, min(1.0, float(reparto_pct_a) / 100.0))
    w_b = 1.0 - w_a

    f_a = factor_orientacion(float(azimut_a_deg), hemisferio=hemisferio)
    f_b = factor_orientacion(float(azimut_b_deg), hemisferio=hemisferio)

    return (w_a * f_a) + (w_b * f_b)


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# delta_azimut_deg()
#   Diferencia angular mínima
#
# factor_orientacion()
#   Factor anual simplificado de orientación
#
# factor_orientacion_total()
#   Factor total considerando techo plano o dos aguas
#
# Consumido por:
# energia.generacion_bruta
#
# ==========================================================
