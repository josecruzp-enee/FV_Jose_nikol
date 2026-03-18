from dataclasses import dataclass
from typing import List, Dict, Any


# ==========================================================
# SALIDA DEL DOMINIO ENERGÍA
# ==========================================================
"""
CONTRATO DE RESULTADO — DOMINIO ENERGÍA
=======================================

Define la estructura oficial de salida del cálculo energético
del sistema fotovoltaico dentro de FV Engine.

Pipeline energético representado:

    generación DC bruta
            ↓
    pérdidas del sistema
            ↓
    energía después de pérdidas
            ↓
    clipping del inversor
            ↓
    energía AC útil

Todas las energías se expresan en kWh.

Modelo soportado:

    ✔ Simulación física horaria (8760)
"""


@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado final del cálculo energético del sistema FV.
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
    Energía AC producida por hora.

    Longitud esperada:
        8760 valores

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

    Ejemplo:

    {
        "motor": "8760",
        "horas": 8760,
        "fuente_clima": "PVGIS",
        "tilt": 15,
        "azimut": 180
    }
    """


# ==========================================================
# ESTRUCTURA DEL RESULTADO
# ==========================================================

"""
Este módulo produce un único objeto:

EnergiaResultado


Estructura:

EnergiaResultado
    ├─ pdc_instalada_kw
    ├─ pac_nominal_kw
    ├─ dc_ac_ratio
    │
    ├─ energia_horaria_kwh (8760)
    │
    ├─ energia_bruta_12m
    ├─ energia_perdidas_12m
    ├─ energia_despues_perdidas_12m
    ├─ energia_clipping_12m
    ├─ energia_util_12m
    │
    ├─ energia_bruta_anual
    ├─ energia_perdidas_anual
    ├─ energia_despues_perdidas_anual
    ├─ energia_clipping_anual
    ├─ energia_util_anual
    │
    ├─ produccion_especifica_kwh_kwp
    ├─ performance_ratio
    │
    ├─ errores
    └─ meta
"""
