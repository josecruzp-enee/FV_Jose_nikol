from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class PerdidasInput:
    potencia_kw: List[float]

    perdidas_dc_pct: float
    sombras_pct: float


@dataclass(frozen=True)
class PerdidasResultado:
    potencia_kw: List[float]
    factor_total: float


def aplicar_perdidas_fisicas(inp: PerdidasInput) -> PerdidasResultado:

    if len(inp.potencia_kw) not in (8760, 8784):
        raise ValueError("Serie inválida")

    if not (0 <= inp.perdidas_dc_pct <= 100):
        raise ValueError("perdidas_dc_pct inválido")

    if not (0 <= inp.sombras_pct <= 100):
        raise ValueError("sombras_pct inválido")

    f_total = (
        (1 - inp.perdidas_dc_pct / 100.0)
        * (1 - inp.sombras_pct / 100.0)
    )

    f_total = max(0.0, min(1.0, f_total))

    potencia_out = [
        max(0.0, p * f_total)
        for p in inp.potencia_kw
    ]

    return PerdidasResultado(
        potencia_kw=potencia_out,
        factor_total=f_total
    )
