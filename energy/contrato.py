from dataclasses import dataclass
from typing import List, Dict, Any

# ==========================================================
# SALIDA DEL DOMINIO ENERGÍA
# ==========================================================
@dataclass(frozen=True)
class EnergiaResultado:
    ok: bool
    errores: List[str]

    # Potencia del sistema
    pdc_instalada_kw: float
    pac_nominal_kw: float
    dc_ac_ratio: float

    # Energía horaria (8760)
    energia_horaria_kwh: List[float]

    # Energía mensual
    energia_bruta_12m: List[float]
    energia_perdidas_12m: List[float]
    energia_despues_perdidas_12m: List[float]
    energia_clipping_12m: List[float]
    energia_util_12m: List[float]

    # Energía anual
    energia_bruta_anual: float
    energia_perdidas_anual: float
    energia_despues_perdidas_anual: float
    energia_clipping_anual: float
    energia_util_anual: float

    # Indicadores
    produccion_especifica_kwh_kwp: float
    performance_ratio: float

    # Metadata / trazabilidad
    meta: Dict[str, Any]
