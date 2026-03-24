from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado final del cálculo energético del sistema FV (8760).

    Flujo representado:

        DC bruta
            ↓
        pérdidas DC
            ↓
        DC neta → inversor
            ↓
        AC sin clipping
            ↓
        clipping inversor
            ↓
        pérdidas AC
            ↓
        AC útil final

    Todas las energías en kWh.
    """

    # ======================================================
    # ESTADO
    # ======================================================
    ok: bool
    errores: List[str]

    # ======================================================
    # SISTEMA
    # ======================================================
    pdc_instalada_kw: float
    pac_nominal_kw: float
    dc_ac_ratio: float

    # ======================================================
    # ENERGÍA HORARIA (8760)
    # ======================================================
    energia_horaria_kwh: List[float]
    """
    Energía AC útil final por hora (post inversor y pérdidas AC).

    Longitud: 8760
    Unidad: kWh
    """

    # ======================================================
    # ENERGÍA MENSUAL (kWh)
    # ======================================================

    # DC antes de pérdidas
    energia_bruta_12m: List[float]

    # AC después de pérdidas (DC+AC) pero antes de clipping
    energia_despues_perdidas_12m: List[float]

    # Pérdidas físicas (DC + AC)
    energia_perdidas_12m: List[float]

    # Pérdidas por clipping del inversor
    energia_clipping_12m: List[float]

    # Energía final útil AC
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
    """
    energia_util_anual / pdc_instalada_kw
    """

    performance_ratio: float
    """
    energia_util_anual / energia_bruta_anual
    """

    # ======================================================
    # METADATA
    # ======================================================
    meta: Dict[str, Any]
    """
    Información de trazabilidad del cálculo.

    Ejemplo:
    {
        "modelo": "8760_alineado",
        "pipeline": "dc→perdidas→inv→ac",
        "horas": 8760
    }
    """
