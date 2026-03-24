from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True)
class EnergiaResultado:
    ok: bool
    errores: List[str]

    # ======================================================
    # CONFIGURACIÓN DEL SISTEMA
    # ======================================================
    pdc_instalada_kw: float
    pac_nominal_kw: float
    dc_ac_ratio: float

    # ======================================================
    # ENERGÍA HORARIA (8760)
    # Siempre en kWh (1 valor = 1 hora integrada)
    # ======================================================
    energia_horaria_kwh: List[float]

    # ======================================================
    # ENERGÍA MENSUAL (kWh)
    # ======================================================

    # Energía DC antes de pérdidas
    energia_bruta_12m: List[float]

    # Energía después de pérdidas DC + AC (ANTES de clipping)
    energia_despues_perdidas_12m: List[float]

    # Pérdidas físicas (DC + AC)
    energia_perdidas_12m: List[float]

    # Pérdidas por clipping del inversor
    energia_clipping_12m: List[float]

    # Energía final útil AC (después de TODO)
    energia_util_12m: List[float]

    # ======================================================
    # ENERGÍA ANUAL (kWh)
    # ======================================================
    energia_bruta_anual: float
    energia_despues_perdidas_anual: float
    energia_perdidas_anual: float
    energia_clipping_anual: float
    energia_util_anual: float

    # ======================================================
    # KPIs
    # ======================================================
    produccion_especifica_kwh_kwp: float
    performance_ratio: float

    # ======================================================
    # TRAZABILIDAD
    # ======================================================
    meta: Dict[str, Any]
