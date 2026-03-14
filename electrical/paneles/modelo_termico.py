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
Modelo térmico basado en NOCT.

Ecuación:

    T_cell = T_ambient + (NOCT - 20) / 800 * G_POA

Donde:

    T_cell      = temperatura de la celda (°C)
    T_ambient   = temperatura ambiente (°C)
    NOCT        = temperatura nominal de operación del módulo (°C)
    G_POA       = irradiancia en el plano del panel (W/m²)

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
    Parámetros de entrada del modelo térmico.
    """

    irradiancia_poa_wm2: float
    temperatura_ambiente_c: float
    noct_c: float


@dataclass
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

    Parámetros
    ----------
    inp : ModeloTermicoInput
        Datos de irradiancia, temperatura ambiente
        y parámetro NOCT del módulo.

    Retorna
    -------
    ModeloTermicoResultado
        Temperatura estimada de la celda FV.
    """

    # ------------------------------------------------------
    # Lectura de parámetros de entrada
    # ------------------------------------------------------

    poa = inp.irradiancia_poa_wm2
    tamb = inp.temperatura_ambiente_c
    noct = inp.noct_c

    # ------------------------------------------------------
    # Validaciones básicas de seguridad
    # ------------------------------------------------------

    if poa < 0:
        raise ValueError("irradiancia_poa_wm2 no puede ser negativa")

    if noct <= 0:
        raise ValueError("noct_c inválido")

    # ------------------------------------------------------
    # Modelo térmico NOCT
    # ------------------------------------------------------
    # T_cell = Tamb + (NOCT - 20)/800 * G_POA
    # ------------------------------------------------------

    t_cell = tamb + ((noct - 20) / 800) * poa

    # ------------------------------------------------------
    # Resultado
    # ------------------------------------------------------

    return ModeloTermicoResultado(
        temperatura_celda_c=t_cell
    )
