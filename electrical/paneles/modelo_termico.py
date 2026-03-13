"""
MODELO TÉRMICO DEL MÓDULO FV — FV Engine

Dominio: panel

Responsabilidad
---------------
Calcular la temperatura de la celda fotovoltaica en función de:

• irradiancia en plano del panel (POA)
• temperatura ambiente
• parámetro NOCT del módulo

Modelo utilizado
----------------
Modelo térmico basado en NOCT.

T_cell = T_ambient + (NOCT - 20)/800 * G_POA

Este modelo es ampliamente utilizado en simulaciones
energéticas preliminares de sistemas fotovoltaicos.
"""

from dataclasses import dataclass


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass
class ModeloTermicoInput:
    """
    Parámetros de entrada del modelo térmico
    """

    irradiancia_poa_wm2: float
    temperatura_ambiente_c: float
    noct_c: float


@dataclass
class ModeloTermicoResultado:
    """
    Resultado del cálculo térmico
    """

    temperatura_celda_c: float


# ==========================================================
# MOTOR TÉRMICO
# ==========================================================

def calcular_temperatura_celda(inp: ModeloTermicoInput) -> ModeloTermicoResultado:
    """
    Calcula la temperatura de la celda FV.
    """

    g = inp.irradiancia_poa_wm2
    tamb = inp.temperatura_ambiente_c
    noct = inp.noct_c

    # modelo térmico NOCT
    t_cell = tamb + ((noct - 20) / 800) * g

    return ModeloTermicoResultado(
        temperatura_celda_c=t_cell
    )
