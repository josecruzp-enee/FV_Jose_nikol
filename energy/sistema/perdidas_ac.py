from dataclasses import dataclass


@dataclass(frozen=True)
class PerdidasACInput:
    potencia_kw: float
    perdidas_ac_pct: float


@dataclass(frozen=True)
class PerdidasACResultado:
    potencia_kw: float
    factor_ac: float


def aplicar_perdidas_ac(inp: PerdidasACInput) -> PerdidasACResultado:

    if inp.potencia_kw < 0:
        raise ValueError("potencia_kw inválida")

    if not (0 <= inp.perdidas_ac_pct <= 100):
        raise ValueError("perdidas_ac_pct inválido")

    f_ac = 1 - inp.perdidas_ac_pct / 100.0
    f_ac = max(0.0, min(1.0, f_ac))

    potencia_out = max(0.0, inp.potencia_kw * f_ac)

    return PerdidasACResultado(
        potencia_kw=potencia_out,
        factor_ac=f_ac
    )
