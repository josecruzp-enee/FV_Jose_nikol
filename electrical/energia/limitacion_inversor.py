from __future__ import annotations

from dataclasses import dataclass
from typing import List


Vector12 = List[float]


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class CurtailmentResultado:

    ok: bool
    errores: List[str]

    energia_final_12m_kwh: Vector12
    energia_recortada_12m_kwh: Vector12

    energia_recortada_anual_kwh: float


# ==========================================================
# API PUBLICA
# ==========================================================

def aplicar_curtailment(
    *,
    energia_12m: Vector12,
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

    energia_final: Vector12 = []
    energia_recortada: Vector12 = []

    if not errores:

        # --------------------------------------------------
        # Sin limitación
        # --------------------------------------------------

        if not permitir or kw_ac <= 0:

            energia_final = list(energia_12m)
            energia_recortada = [0.0] * 12

        else:

            ratio = float(pdc_kw) / float(kw_ac)

            if ratio <= 1.0:

                energia_final = list(energia_12m)
                energia_recortada = [0.0] * 12

            else:

                # --------------------------------------------------
                # Modelo físico simplificado de clipping
                # --------------------------------------------------

                loss_clip = 0.5 * (ratio - 1.0) ** 2

                loss_clip = max(0.0, min(0.15, loss_clip))

                for i in range(12):

                    e = float(energia_12m[i])

                    r = e * loss_clip

                    energia_recortada.append(r)
                    energia_final.append(max(0.0, e - r))

    energia_recortada_anual = sum(energia_recortada)

    ok = len(errores) == 0

    return CurtailmentResultado(
        ok=ok,
        errores=errores,
        energia_final_12m_kwh=energia_final,
        energia_recortada_12m_kwh=energia_recortada,
        energia_recortada_anual_kwh=energia_recortada_anual,
    )
