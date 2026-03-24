from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ==========================================================
# UNITARIO (USADO POR ORQUESTADOR)
# ==========================================================

@dataclass(frozen=True)
class InversorInput:
    potencia_dc_kw: float
    p_ac_nominal_kw: float
    eficiencia_nominal: float = 0.97


@dataclass(frozen=True)
class InversorResultado:
    potencia_ac_kw: float              # con clipping
    potencia_ac_sin_clip_kw: float     # 🔥 clave física
    clipping_kw: float


def calcular_inversor(inp: InversorInput) -> InversorResultado:

    if inp.potencia_dc_kw < 0:
        raise ValueError("potencia_dc_kw inválida")

    if inp.p_ac_nominal_kw <= 0:
        raise ValueError("p_ac_nominal_kw inválido")

    if not (0 < inp.eficiencia_nominal <= 1):
        raise ValueError("eficiencia_nominal inválida")

    # ---------------------------------------------
    # DC → AC (sin límite)
    # ---------------------------------------------
    p_ac_raw = inp.potencia_dc_kw * inp.eficiencia_nominal

    # ---------------------------------------------
    # CLIPPING
    # ---------------------------------------------
    if p_ac_raw > inp.p_ac_nominal_kw:
        p_ac = inp.p_ac_nominal_kw
        clipping = p_ac_raw - p_ac
    else:
        p_ac = p_ac_raw
        clipping = 0.0

    return InversorResultado(
        potencia_ac_kw=p_ac,
        potencia_ac_sin_clip_kw=p_ac_raw,
        clipping_kw=clipping
    )


# ==========================================================
# 8760 (ANÁLISIS COMPLETO)
# ==========================================================

@dataclass(frozen=True)
class Inversor8760Input:
    potencia_dc_kw: List[float]
    p_ac_nominal_kw: float
    eficiencia_nominal: float = 0.97


@dataclass(frozen=True)
class Inversor8760Resultado:
    potencia_ac_kw: List[float]
    potencia_ac_sin_clip_kw: List[float]
    clipping_kw: List[float]

    energia_ac_anual_kwh: float
    energia_clipping_anual_kwh: float


def calcular_inversor_8760(inp: Inversor8760Input) -> Inversor8760Resultado:

    if len(inp.potencia_dc_kw) not in (8760, 8784):
        raise ValueError("Serie DC inválida")

    if inp.p_ac_nominal_kw <= 0:
        raise ValueError("p_ac_nominal_kw inválido")

    if not (0 < inp.eficiencia_nominal <= 1):
        raise ValueError("eficiencia_nominal inválida")

    potencia_ac = []
    potencia_ac_sin_clip = []
    clipping = []

    for p_dc in inp.potencia_dc_kw:

        # usar modelo unitario → consistencia total
        res = calcular_inversor(
            InversorInput(
                potencia_dc_kw=p_dc,
                p_ac_nominal_kw=inp.p_ac_nominal_kw,
                eficiencia_nominal=inp.eficiencia_nominal
            )
        )

        potencia_ac.append(res.potencia_ac_kw)
        potencia_ac_sin_clip.append(res.potencia_ac_sin_clip_kw)
        clipping.append(res.clipping_kw)

    energia_ac = sum(potencia_ac)
    energia_clip = sum(clipping)

    return Inversor8760Resultado(
        potencia_ac_kw=potencia_ac,
        potencia_ac_sin_clip_kw=potencia_ac_sin_clip,
        clipping_kw=clipping,
        energia_ac_anual_kwh=energia_ac,
        energia_clipping_anual_kwh=energia_clip
    )
