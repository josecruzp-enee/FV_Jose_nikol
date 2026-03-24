from dataclasses import dataclass
from typing import List, Dict, Any


# ==========================================================
# SALIDA DEL DOMINIO ENERGÍA
# ==========================================================
"""
CONTRATO DE RESULTADO — DOMINIO ENERGÍA
=======================================

Define la estructura oficial del resultado del motor energético FV.

Pipeline representado:

    generación DC bruta
            ↓
    pérdidas del sistema (DC)
            ↓
    energía DC después de pérdidas
            ↓
    clipping del inversor
            ↓
    pérdidas AC
            ↓
    energía AC útil

Todas las energías se expresan en kWh.

Modelo soportado:
    ✔ Simulación horaria 8760
"""


# ==========================================================
# RESULTADO PRINCIPAL
# ==========================================================
@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado final del cálculo energético del sistema FV.

    Este objeto es la salida única del dominio energía.
    """


    # ------------------------------------------------------
    # ESTADO DEL CÁLCULO
    # ------------------------------------------------------
    ok: bool
    errores: List[str]


    # ------------------------------------------------------
    # POTENCIA DEL SISTEMA
    # ------------------------------------------------------
    pdc_instalada_kw: float
    pac_nominal_kw: float


    # ------------------------------------------------------
    # RELACIÓN DC / AC
    # ------------------------------------------------------
    dc_ac_ratio: float


    # ------------------------------------------------------
    # ENERGÍA HORARIA (8760)
    # ------------------------------------------------------
    energia_horaria_kwh: List[float]
    """
    Energía AC útil por hora.

    ✔ Siempre representa la salida final del sistema (post inversor y pérdidas AC)

    Longitud esperada:
        8760

    Unidad:
        kWh
    """


    # ------------------------------------------------------
    # ENERGÍA MENSUAL (12 MESES)
    # ------------------------------------------------------
    energia_bruta_12m: List[float]
    energia_perdidas_12m: List[float]
    energia_despues_perdidas_12m: List[float]
    energia_clipping_12m: List[float]
    energia_util_12m: List[float]
    """
    Todas las listas deben tener longitud 12 (enero–diciembre).
    """


    # ------------------------------------------------------
    # ENERGÍA ANUAL
    # ------------------------------------------------------
    energia_bruta_anual: float
    energia_perdidas_anual: float
    energia_despues_perdidas_anual: float
    energia_clipping_anual: float
    energia_util_anual: float


    # ------------------------------------------------------
    # INDICADORES ENERGÉTICOS
    # ------------------------------------------------------
    produccion_especifica_kwh_kwp: float
    """
    Producción específica:

        energia_util_anual / pdc_instalada_kw
    """

    performance_ratio: float
    """
    Performance Ratio:

        energia_util_anual / energia_bruta_anual
    """


    # ------------------------------------------------------
    # METADATA
    # ------------------------------------------------------
    meta: Dict[str, Any]
    """
    Información de trazabilidad del cálculo.

    Campos recomendados:

    {
        "motor": "8760",
        "horas": 8760,
        "fuente_clima": "...",
        "tilt": float,
        "azimut": float
    }
    """


# ==========================================================
# NOTA DE DISEÑO
# ==========================================================
"""
Este contrato:

✔ No contiene lógica
✔ No contiene defaults
✔ No contiene validaciones físicas

Solo define estructura de salida.

El orquestador es responsable de:
    - coherencia de datos
    - consistencia de longitudes
    - cálculos físicos

Esto mantiene el diseño limpio y escalable.
"""
