from __future__ import annotations

"""
CONTRATO DEL DOMINIO ENERGÍA — FV Engine
========================================

Define las estructuras formales de entrada y salida del
motor energético fotovoltaico.

Este módulo NO contiene lógica de cálculo.

Responsabilidad
---------------
Definir los contratos de datos utilizados por el dominio
energía para ejecutar los modelos energéticos del sistema FV.

El motor energético soporta dos modos de simulación:

    1) Modelo energético mensual basado en HSP
    2) Simulación física horaria (8760)

Consumido por:
    core.aplicacion.orquestador_estudio
    reportes
    finanzas
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Literal


# ==========================================================
# ENTRADA DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaInput:
    """
    Entrada formal del motor energético FV.

    Este modelo agrupa todos los parámetros necesarios
    para ejecutar cualquiera de los modelos energéticos
    disponibles en FV Engine.

    Modelos soportados:

        • "mensual" → modelo energético basado en HSP
        • "8760"    → simulación física horaria completa

    El orquestador energético seleccionará el modelo
    dependiendo del campo `modo_simulacion`.
    """

    # ------------------------------------------------------
    # POTENCIAS DEL SISTEMA FV
    # ------------------------------------------------------

    # Potencia DC total instalada del generador FV (kW)
    pdc_instalada_kw: float

    # Potencia AC nominal total de los inversores (kW)
    pac_nominal_kw: float


    # ------------------------------------------------------
    # MODO DE SIMULACIÓN
    # ------------------------------------------------------

    # Tipo de modelo energético a ejecutar
    #
    # "mensual" → modelo simplificado HSP
    # "8760"    → simulación física horaria
    modo_simulacion: Literal["mensual", "8760"] = "mensual"


    # ------------------------------------------------------
    # RECURSO SOLAR — MODELO HSP
    # ------------------------------------------------------

    # Peak Sun Hours promedio mensual
    #
    # unidades:
    # kWh/m²/día
    #
    # longitud esperada: 12 valores (enero → diciembre)
    hsp_12m: List[float] | None = None

    # número de días de cada mes
    #
    # longitud esperada: 12 valores
    dias_mes: List[int] | None = None


    # ------------------------------------------------------
    # PARÁMETROS GEOGRÁFICOS — MODELO 8760
    # ------------------------------------------------------

    # latitud del sitio (grados)
    latitud: float | None = None

    # longitud del sitio (grados)
    longitud: float | None = None


    # ------------------------------------------------------
    # FACTORES DEL SISTEMA FV
    # ------------------------------------------------------

    # factor energético por orientación del generador
    #
    # típicamente entre:
    # 0.85 – 1.0
    factor_orientacion: float = 1.0

    # pérdidas DC del sistema (%)
    #
    # incluye:
    # mismatch
    # cables DC
    # tolerancias de módulo
    perdidas_dc_pct: float = 0.0

    # pérdidas AC del sistema (%)
    #
    # incluye:
    # cables AC
    # transformadores
    perdidas_ac_pct: float = 0.0

    # pérdidas por sombras (%)
    sombras_pct: float = 0.0


    # ------------------------------------------------------
    # CONTROL DE CURTAILMENT
    # ------------------------------------------------------

    # permite pérdidas por clipping DC/AC
    permitir_curtailment: bool = True


    # ------------------------------------------------------
    # PARÁMETROS TÉRMICOS (MODELOS FÍSICOS)
    # ------------------------------------------------------

    # temperatura ambiente promedio (°C)
    #
    # usado únicamente en modelos físicos
    # como el simulador 8760
    temp_ambiente_c: float = 25.0



# ==========================================================
# RESULTADO DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaResultado:
    """
    Resultado formal del motor energético FV.

    Contiene la producción energética del sistema
    tanto a nivel mensual como anual.

    Este resultado es consumido por:

        • módulo financiero
        • generador de reportes
        • visualización en UI
    """

    # ------------------------------------------------------
    # ESTADO DEL CÁLCULO
    # ------------------------------------------------------

    ok: bool

    # lista de errores ocurridos durante la simulación
    errores: List[str]


    # ------------------------------------------------------
    # POTENCIAS DEL SISTEMA
    # ------------------------------------------------------

    # potencia DC total instalada (kW)
    pdc_instalada_kw: float

    # potencia AC nominal del inversor (kW)
    pac_nominal_kw: float

    # relación DC/AC del sistema
    dc_ac_ratio: float


    # ------------------------------------------------------
    # ENERGÍA MENSUAL
    # ------------------------------------------------------

    # energía DC generada antes de pérdidas
    energia_bruta_12m: List[float]

    # energía después de pérdidas físicas
    energia_despues_perdidas_12m: List[float]

    # energía perdida por clipping del inversor
    energia_curtailment_12m: List[float]

    # energía AC final entregada por el sistema
    energia_util_12m: List[float]


    # ------------------------------------------------------
    # ENERGÍA ANUAL
    # ------------------------------------------------------

    # energía anual bruta (kWh)
    energia_bruta_anual: float

    # energía anual útil entregada (kWh)
    energia_util_anual: float

    # energía anual perdida por clipping
    energia_curtailment_anual: float


    # ------------------------------------------------------
    # METADATA DEL CÁLCULO
    # ------------------------------------------------------

    # información adicional del modelo energético
    #
    # ejemplos:
    # modelo usado
    # factores aplicados
    # métricas internas
    meta: Dict[str, Any] = field(default_factory=dict)
