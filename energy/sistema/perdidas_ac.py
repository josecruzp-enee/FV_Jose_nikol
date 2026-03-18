from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class PerdidasACInput:
    potencia_kw: List[float]
    perdidas_ac_pct: float


@dataclass(frozen=True)
class PerdidasACResultado:
    potencia_kw: List[float]
    factor_ac: float


def aplicar_perdidas_ac(inp: PerdidasACInput) -> PerdidasACResultado:

    if len(inp.potencia_kw) not in (8760, 8784):
        raise ValueError("Serie inválida")

    if not (0 <= inp.perdidas_ac_pct <= 100):
        raise ValueError("perdidas_ac_pct inválido")

    f_ac = 1 - inp.perdidas_ac_pct / 100.0
    f_ac = max(0.0, min(1.0, f_ac))

    potencia_out = [
        max(0.0, p * f_ac)
        for p in inp.potencia_kw
    ]

    return PerdidasACResultado(
        potencia_kw=potencia_out,
        factor_ac=f_ac
    )
