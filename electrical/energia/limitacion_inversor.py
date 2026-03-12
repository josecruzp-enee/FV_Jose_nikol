from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class CurtailmentResultado:

    ok: bool
    errores: List[str]

    energia_final_12m_kwh: List[float]
    energia_recortada_12m_kwh: List[float]


# ==========================================================
# API PUBLICA
# ==========================================================

def aplicar_curtailment(
    *,
    energia_12m: List[float],
    pdc_kw: float,
    kw_ac: float,
    permitir: bool,
) -> CurtailmentResultado:

    errores: List[str] = []

    if len(energia_12m) != 12:
        errores.append("energia_12m debe tener 12 valores.")

    if pdc_kw < 0:
        errores.append("pdc_kw inválido.")

    if kw_ac < 0:
        errores.append("kw_ac inválido.")

    energia_final: List[float] = []
    energia_recortada: List[float] = []

    if not errores:

        # ------------------------------------------
        # Sin limitación
        # ------------------------------------------

        if not permitir or kw_ac <= 0:

            energia_final = list(energia_12m)
            energia_recortada = [0.0] * 12

        else:

            ratio = float(pdc_kw) / float(kw_ac)

            if ratio <= 1.0:

                energia_final = list(energia_12m)
                energia_recortada = [0.0] * 12

            else:

                # ------------------------------------------
                # Modelo simple de clipping
                # ------------------------------------------

                exceso_factor = min(1.0, (ratio - 1.0) * 0.5)

                energia_recortada = [
                    float(e) * exceso_factor for e in energia_12m
                ]

                energia_final = [
                    float(e) - r for e, r in zip(energia_12m, energia_recortada)
                ]

    ok = len(errores) == 0

    return CurtailmentResultado(
        ok=ok,
        errores=errores,
        energia_final_12m_kwh=energia_final,
        energia_recortada_12m_kwh=energia_recortada,
    )


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# CurtailmentResultado
#
# Campos:
#
# ok : bool
# errores : list[str]
# energia_final_12m_kwh : list[float]
# energia_recortada_12m_kwh : list[float]
#
# Descripción:
# Energía mensual después de aplicar limitación del inversor
# (clipping DC/AC).
#
# energia_recortada_12m_kwh representa la energía perdida
# por saturación del inversor.
#
# Consumido por:
# energia.orquestador_energia
#
# ==========================================================
