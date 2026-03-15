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

Este contrato transporta la información energética producida
por el orquestador energético.

Pipeline energético representado:

    generación DC bruta
            ↓
    pérdidas del sistema
            ↓
    energía disponible después de pérdidas
            ↓
    clipping del inversor
            ↓
    energía AC útil

Todas las energías se expresan en kWh.
"""


@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado final del cálculo energético del sistema FV.
    """

    # ------------------------------------------------------
    # Estado del cálculo
    # ------------------------------------------------------

    ok: bool
    # Indica si el cálculo energético se ejecutó correctamente.

    errores: List[str]
    # Lista de errores ocurridos durante la ejecución del motor.


    # ------------------------------------------------------
    # Potencias nominales del sistema
    # ------------------------------------------------------

    pdc_instalada_kw: float
    # Potencia DC total instalada del generador FV.

    pac_nominal_kw: float
    # Potencia AC nominal total del inversor.


    # ------------------------------------------------------
    # Relación DC / AC
    # ------------------------------------------------------

    dc_ac_ratio: float
    # Relación entre potencia DC instalada y potencia AC del inversor.


    # ------------------------------------------------------
    # Energía mensual (12 meses)
    # ------------------------------------------------------

    energia_bruta_12m: List[float]
    # Energía DC generada antes de pérdidas del sistema.

    energia_perdidas_12m: List[float]
    # Energía perdida por efectos físicos del sistema.

    energia_despues_perdidas_12m: List[float]
    # Energía disponible después de aplicar pérdidas.

    energia_clipping_12m: List[float]
    # Energía recortada por limitación del inversor (DC/AC clipping).

    energia_util_12m: List[float]
    # Energía AC final disponible del sistema.


    # ------------------------------------------------------
    # Energía anual agregada
    # ------------------------------------------------------

    energia_bruta_anual: float
    # Energía DC anual generada antes de pérdidas.

    energia_perdidas_anual: float
    # Energía anual perdida por efectos físicos del sistema.

    energia_despues_perdidas_anual: float
    # Energía anual disponible después de pérdidas.

    energia_clipping_anual: float
    # Energía anual perdida por clipping del inversor.

    energia_util_anual: float
    # Energía AC anual final disponible.


    # ------------------------------------------------------
    # Indicadores energéticos
    # ------------------------------------------------------

    produccion_especifica_kwh_kwp: float
    # Producción específica del sistema FV.
    #
    # Energía AC anual producida por cada kWp instalado.
    #
    # Fórmula:
    #
    #     energia_util_anual / pdc_instalada_kw
    #
    # Unidad:
    #
    #     kWh/kWp
    #
    # Permite comparar el rendimiento energético del sistema
    # independientemente del tamaño de la planta.


    performance_ratio: float
    # Performance Ratio (PR) del sistema fotovoltaico.
    #
    # Representa la eficiencia global del sistema considerando
    # pérdidas térmicas, eléctricas, conversión del inversor
    # y clipping.
    #
    # Fórmula aproximada usada en el motor:
    #
    #     PR = energia_util_anual / energia_bruta_anual
    #
    # Valores típicos:
    #
    #     0.70 – 0.85


    # ------------------------------------------------------
    # Metadata del cálculo
    # ------------------------------------------------------

    meta: Dict[str, Any]
    # Información adicional del motor energético.
    #
    # Ejemplo:
    #
    # {
    #     "motor": "HSP" | "8760",
    #     "meses": 12,
    #     "factor_orientacion": 0.94
    # }
