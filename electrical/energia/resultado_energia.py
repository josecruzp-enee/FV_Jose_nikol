# ==========================================================
# SALIDA DEL DOMINIO ENERGIA
# ==========================================================

@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado del cálculo energético del sistema FV.
    """

    ok: bool
    errores: List[str]

    # Potencias del sistema
    pdc_instalada_kw: float
    pac_nominal_kw: float

    # Ratio DC/AC
    dc_ac_ratio: float

    # Energía mensual
    energia_bruta_12m: List[float]
    energia_despues_perdidas_12m: List[float]
    energia_curtailment_12m: List[float]
    energia_util_12m: List[float]

    # Energía anual
    energia_bruta_anual: float
    energia_util_anual: float
    energia_curtailment_anual: float

    # Metadata adicional
    meta: dict
