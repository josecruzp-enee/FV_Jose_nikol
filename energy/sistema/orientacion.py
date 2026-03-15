# electrical/energia/orientacion.py

from __future__ import annotations

"""
MODELO SIMPLIFICADO DE ORIENTACIÓN — FV Engine
==============================================

Este módulo calcula el factor de orientación anual del
generador fotovoltaico en función del azimut del sistema.

Responsabilidad
----------------

Estimar la penalización energética causada por una orientación
distinta a la óptima.

Este modelo NO calcula:

• irradiancia
• producción energética
• pérdidas del sistema
• clipping del inversor

Solo devuelve un factor correctivo para el modelo HSP.

Uso dentro del motor energético
-------------------------------

    orientacion
        ↓
    generacion_bruta
        ↓
    pérdidas
        ↓
    modelo inversor

Modelo físico simplificado
--------------------------

Se utiliza una penalización coseno suavizada respecto a la
orientación óptima.

    factor = (1 + cos(Δazimut)) / 2

Se limita el valor mínimo para evitar penalizaciones
excesivas en modelos simplificados.
"""

import math


# ==========================================================
# UTILIDADES ANGULARES
# ==========================================================

def delta_azimut_deg(az_deg: float, ref_deg: float = 180.0) -> float:
    """
    Calcula la diferencia angular mínima entre dos azimuts.

    Maneja correctamente la continuidad circular 0–360°.

    Parámetros
    ----------
    az_deg : float
        Azimut del sistema FV

    ref_deg : float
        Azimut de referencia (orientación óptima)

    Retorna
    -------
    float
        Diferencia angular mínima en grados
    """

    d = abs(float(az_deg) - float(ref_deg)) % 360.0

    return min(d, 360.0 - d)


# ==========================================================
# FACTOR ORIENTACION SIMPLE
# ==========================================================

def factor_orientacion(
    az_deg: float,
    hemisferio: str = "norte"
) -> float:
    """
    Calcula el factor anual simplificado por orientación.

    Parámetros
    ----------
    az_deg : float
        Azimut del generador FV (°)

    hemisferio : str
        "norte" o "sur"

    Retorna
    -------
    float
        Factor entre 0.35 y 1.0
    """

    # protección contra valores nulos
    hem = (hemisferio or "norte").lower()

    # orientación óptima según hemisferio
    ref = 0.0 if hem == "sur" else 180.0

    delta = delta_azimut_deg(az_deg, ref)

    # modelo coseno suavizado
    f = (1.0 + math.cos(math.radians(delta))) / 2.0

    # límites físicos del modelo simplificado
    return max(0.35, min(1.0, f))


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
    Calcula el factor total considerando diferentes
    configuraciones de superficie.

    Casos soportados
    ----------------

    1) Superficie plana
    2) Techo dos aguas (promedio ponderado)

    Parámetros
    ----------
    tipo_superficie : str
        "plano" o "dos_aguas"

    azimut_deg : float
        Azimut principal del generador

    azimut_a_deg : float
        Azimut del lado A del techo

    azimut_b_deg : float
        Azimut del lado B del techo

    reparto_pct_a : float
        Porcentaje de paneles en lado A

    hemisferio : str
        "norte" o "sur"

    Retorna
    -------
    float
        Factor de orientación global
    """

    tipo = str(tipo_superficie or "plano").lower()

    # ------------------------------------------
    # CASO SUPERFICIE PLANA
    # ------------------------------------------

    if tipo != "dos_aguas":

        return factor_orientacion(
            azimut_deg,
            hemisferio=hemisferio
        )

    # ------------------------------------------
    # FALLBACK SEGURO
    # ------------------------------------------

    if (
        azimut_a_deg is None
        or azimut_b_deg is None
        or reparto_pct_a is None
    ):

        return factor_orientacion(
            azimut_deg,
            hemisferio=hemisferio
        )

    # ------------------------------------------
    # CÁLCULO PONDERADO
    # ------------------------------------------

    w_a = max(0.0, min(1.0, float(reparto_pct_a) / 100.0))
    w_b = 1.0 - w_a

    f_a = factor_orientacion(
        float(azimut_a_deg),
        hemisferio=hemisferio
    )

    f_b = factor_orientacion(
        float(azimut_b_deg),
        hemisferio=hemisferio
    )

    return (w_a * f_a) + (w_b * f_b)


# ==========================================================
# SALIDAS DEL MÓDULO
# ==========================================================

"""
delta_azimut_deg()
    Diferencia angular mínima entre dos azimuts.

factor_orientacion()
    Factor anual simplificado por orientación.

factor_orientacion_total()
    Factor total considerando:
        • superficie plana
        • techo dos aguas

Consumido por:

    energia.generacion_bruta
"""
