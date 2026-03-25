from dataclasses import dataclass


@dataclass(frozen=True)
class PerdidasACInput:
    potencia_kw: float
    perdidas_ac_frac: float  # 0–1


@dataclass(frozen=True)
class PerdidasACResultado:
    potencia_kw: float
    factor_ac: float
    perdida_kw: float


def aplicar_perdidas_ac(inp: PerdidasACInput) -> PerdidasACResultado:

    # --------------------------------------------------
    # VALIDACIONES
    # --------------------------------------------------
    if inp.potencia_kw < 0:
        raise ValueError("potencia_kw inválida")

    if not (0 <= inp.perdidas_ac_frac <= 1):
        raise ValueError("perdidas_ac_frac debe estar entre 0 y 1")

    # --------------------------------------------------
    # CÁLCULO
    # --------------------------------------------------
    f_ac = 1.0 - inp.perdidas_ac_frac

    # clamp de seguridad (por si hay ruido numérico)
    f_ac = max(0.0, min(1.0, f_ac))

    potencia_out = max(0.0, inp.potencia_kw * f_ac)
    perdida_kw = inp.potencia_kw - potencia_out

    # --------------------------------------------------
    # RESULTADO
    # --------------------------------------------------
    return PerdidasACResultado(
        potencia_kw=potencia_out,
        factor_ac=f_ac,
        perdida_kw=perdida_kw
    )
