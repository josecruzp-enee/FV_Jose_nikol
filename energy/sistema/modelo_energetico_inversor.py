from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ==========================================================
# ENTRADA
# ==========================================================

@dataclass(frozen=True)
class Inversor8760Input:

    potencia_dc_kw: List[float]
    p_ac_nominal_kw: float
    eficiencia_nominal: float = 0.97


# ==========================================================
# SALIDA
# ==========================================================

@dataclass(frozen=True)
class Inversor8760Resultado:

    potencia_ac_kw: List[float]
    clipping_kw: List[float]

    energia_ac_anual_kwh: float
    energia_clipping_anual_kwh: float


# ==========================================================
# MOTOR
# ==========================================================
def calcular_inversor_8760(inp: Inversor8760Input) -> Inversor8760Resultado:

    if len(inp.potencia_dc_kw) not in (8760, 8784):
        raise ValueError("Serie DC inválida")

    if inp.p_ac_nominal_kw <= 0:
        raise ValueError("p_ac_nominal_kw inválido")

    if not (0 < inp.eficiencia_nominal <= 1):
        raise ValueError("eficiencia_nominal inválida")

    potencia_ac = []
    clipping = []

    for p_dc in inp.potencia_dc_kw:

        # ---------------------------------------------
        # EFICIENCIA (DC → AC)
        # ---------------------------------------------

        p_ac_raw = p_dc * inp.eficiencia_nominal

        # ---------------------------------------------
        # CLIPPING EN AC
        # ---------------------------------------------

        if p_ac_raw > inp.p_ac_nominal_kw:
            p_ac = inp.p_ac_nominal_kw
            clip = p_ac_raw - inp.p_ac_nominal_kw
        else:
            p_ac = p_ac_raw
            clip = 0.0

        potencia_ac.append(p_ac)
        clipping.append(clip)

    energia_ac = sum(potencia_ac)
    energia_clip = sum(clipping)

    return Inversor8760Resultado(
        potencia_ac_kw=potencia_ac,
        clipping_kw=clipping,
        energia_ac_anual_kwh=energia_ac,
        energia_clipping_anual_kwh=energia_clip
    )
