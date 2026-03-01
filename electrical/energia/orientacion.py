from __future__ import annotations
import math


# ==========================================================
# Utilidades angulares
# ==========================================================

def delta_azimut_deg(az_deg: float, ref_deg: float = 180.0) -> float:
    """
    Diferencia angular mínima entre azimut y referencia.
    Maneja continuidad circular (0–360°).
    """
    d = abs(float(az_deg) - float(ref_deg)) % 360.0
    return min(d, 360.0 - d)


# ==========================================================
# Factor orientación simple (anual)
# ==========================================================

def factor_orientacion(az_deg: float, hemisferio: str = "norte") -> float:
    """
    Factor anual simplificado por orientación.

    - Óptimo: Sur (180°) en hemisferio norte
    - Óptimo: Norte (0°) en hemisferio sur
    - Modelo coseno suavizado
    - Penalización realista (mínimo 35%)
    """

    ref = 0.0 if hemisferio.lower() == "sur" else 180.0
    delta = delta_azimut_deg(az_deg, ref)

    f = (1.0 + math.cos(math.radians(delta))) / 2.0

    return max(0.35, min(1.00, f))


# ==========================================================
# Factor orientación total (plano o dos aguas)
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
    Devuelve factor total considerando:

    - Superficie plana
    - Techo dos aguas (ponderado energético)

    Siempre devuelve valor válido.
    Nunca lanza excepción.
    """

    tipo = str(tipo_superficie or "plano").lower()

    # ------------------------------------------
    # Caso plano o no definido
    # ------------------------------------------
    if tipo != "dos_aguas":
        return factor_orientacion(azimut_deg, hemisferio=hemisferio)

    # ------------------------------------------
    # Fallback seguro si faltan datos
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
