# electrical/energia/orientacion.py

from __future__ import annotations
import math


def delta_azimut_deg(az_deg: float, ref_deg: float = 180.0) -> float:
    d = abs(float(az_deg) - float(ref_deg)) % 360.0
    return min(d, 360.0 - d)


def factor_orientacion(az_deg: float) -> float:
    delta = delta_azimut_deg(az_deg, 180.0)
    f = (1.0 + math.cos(math.radians(delta))) / 2.0
    return max(0.20, min(1.00, f))


def factor_orientacion_total(
    tipo_superficie: str,
    azimut_deg: float,
    azimut_a_deg: float | None = None,
    azimut_b_deg: float | None = None,
    reparto_pct_a: float | None = None,
) -> float:

    tipo = str(tipo_superficie or "plano").lower()

    if tipo != "dos_aguas":
        return factor_orientacion(azimut_deg)

    if azimut_a_deg is None or azimut_b_deg is None or reparto_pct_a is None:
        raise ValueError("Parámetros incompletos para dos_aguas")

    w_a = max(0.0, min(1.0, float(reparto_pct_a) / 100.0))
    w_b = 1.0 - w_a

    return (
        w_a * factor_orientacion(float(azimut_a_deg))
        + w_b * factor_orientacion(float(azimut_b_deg))
    )
