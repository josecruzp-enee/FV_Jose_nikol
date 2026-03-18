from __future__ import annotations

"""
MODELO TÉRMICO DEL MÓDULO FV — FV Engine

Dominio: paneles / energía

Responsabilidad
---------------
Calcular la temperatura de la celda fotovoltaica a partir de:

• irradiancia en el plano del generador (POA)
• temperatura ambiente
• parámetro térmico NOCT del módulo

Modelo utilizado
----------------
Modelo térmico basado en NOCT:

    T_cell = T_ambient + (NOCT - 20) / 800 * G_POA

Este modelo es estándar en simulaciones FV de nivel ingeniería.
"""

from dataclasses import dataclass


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass(frozen=True)
class ModeloTermicoInput:
    """
    Parámetros de entrada del modelo térmico.
    """

    irradiancia_poa_wm2: float
    temperatura_ambiente_c: float
    noct_c: float


@dataclass(frozen=True)
class ModeloTermicoResultado:
    """
    Resultado del cálculo térmico del módulo FV.
    """

    temperatura_celda_c: float


# ==========================================================
# MOTOR TÉRMICO
# ==========================================================

def calcular_temperatura_celda(inp: ModeloTermicoInput) -> ModeloTermicoResultado:
    """
    Calcula la temperatura de la celda fotovoltaica
    usando el modelo térmico basado en NOCT.

    Modelo:

        T_cell = T_amb + (NOCT - 20)/800 * POA

    Consideraciones:
        - POA = 0 → T_cell ≈ T_amb
        - Modelo válido para simulación 8760 simplificada
    """

    # ------------------------------------------------------
    # LECTURA DE ENTRADA
    # ------------------------------------------------------

    poa = inp.irradiancia_poa_wm2
    tamb = inp.temperatura_ambiente_c
    noct = inp.noct_c

    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if poa < 0:
        raise ValueError("irradiancia_poa_wm2 no puede ser negativa")

    if noct <= 0:
        raise ValueError("noct_c inválido")

    # ------------------------------------------------------
    # SIN IRRADIANCIA → SIN CALENTAMIENTO
    # ------------------------------------------------------

    if poa == 0:
        return ModeloTermicoResultado(
            temperatura_celda_c=tamb
        )

    # ------------------------------------------------------
    # MODELO TÉRMICO NOCT
    # ------------------------------------------------------

    t_cell = tamb + ((noct - 20.0) / 800.0) * poa

    # ------------------------------------------------------
    # RESULTADO
    # ------------------------------------------------------

    return ModeloTermicoResultado(
        temperatura_celda_c=t_cell
    )
