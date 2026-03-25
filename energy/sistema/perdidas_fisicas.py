from dataclasses import dataclass


@dataclass(frozen=True)
class PerdidasInput:
    potencia_kw: float
    perdidas_dc_frac: float
    sombras_frac: float


@dataclass(frozen=True)
class PerdidasResultado:
    potencia_kw: float
    factor_total: float


def aplicar_perdidas_fisicas(inp: PerdidasInput) -> PerdidasResultado:

    if inp.potencia_kw < 0:
        raise ValueError("potencia_kw inválida")

    # 🔥 VALIDACIÓN CORRECTA (FRACCIÓN)
    if not (0 <= inp.perdidas_dc_frac <= 1):
        raise ValueError("perdidas_dc_frac inválido")

    if not (0 <= inp.sombras_frac <= 1):
        raise ValueError("sombras_frac inválido")

    # 🔥 CÁLCULO CORRECTO
    f_total = (
        (1 - inp.perdidas_dc_frac)
        * (1 - inp.sombras_frac)
    )

    f_total = max(0.0, min(1.0, f_total))

    potencia_out = max(0.0, inp.potencia_kw * f_total)

    return PerdidasResultado(
        potencia_kw=potencia_out,
        factor_total=f_total
    )
