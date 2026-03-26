from __future__ import annotations

"""
MODELO DE IRRADIANCIA EN PLANO (POA) — FV Engine
================================================

Responsabilidad
---------------

Convertir irradiancia horizontal (GHI, DNI, DHI) en irradiancia
sobre el plano del generador FV (POA).

Pipeline representado:

    GHI / DNI / DHI
            ↓
    geometría solar
            ↓
    descomposición:
        • componente directa
        • componente difusa
        • componente reflejada
            ↓
    POA total

Modelo implementado
-------------------

    ✔ Modelo isotrópico (Liu & Jordan)

Este modelo es:

    • estable
    • robusto
    • adecuado para simulación inicial

Limitaciones:

    • no considera anisotropía del cielo
    • no modela circumsolar explícito

Frontera del dominio
--------------------

Entrada:
    IrradianciaInput

Salida:
    IrradianciaPlano

Consumido por:
    simulacion_8760 → energy

Reglas arquitectónicas
----------------------

    ✔ no depende de paneles eléctricos
    ✔ no calcula energía
    ✔ no conoce inversores
"""

from dataclasses import dataclass
from math import cos, sin, radians


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass(frozen=True)
class IrradianciaInput:
    """
    Entrada del modelo de irradiancia en plano.
    """

    # ------------------------------------------------------
    # IRRADIANCIA BASE
    # ------------------------------------------------------

    dni: float
    dhi: float
    ghi: float

    # ------------------------------------------------------
    # GEOMETRÍA SOLAR
    # ------------------------------------------------------

    solar_zenith_deg: float
    solar_azimuth_deg: float

    # ------------------------------------------------------
    # GEOMETRÍA DEL PANEL
    # ------------------------------------------------------

    panel_tilt_deg: float
    panel_azimuth_deg: float

    # ------------------------------------------------------
    # ENTORNO
    # ------------------------------------------------------

    albedo: float = 0.2


@dataclass(frozen=True)
class IrradianciaPlano:
    """
    Resultado del modelo POA.
    """

    poa_total: float
    poa_directa: float
    poa_difusa: float
    poa_reflejada: float


# ==========================================================
# ÁNGULO DE INCIDENCIA
# ==========================================================

def _cos_theta_i(inp: IrradianciaInput) -> float:
    """
    Calcula coseno del ángulo de incidencia.

    Representa qué tan perpendicular llega la radiación al panel.
    """

    zen = radians(inp.solar_zenith_deg)
    az = radians(inp.solar_azimuth_deg)

    tilt = radians(inp.panel_tilt_deg)
    panel_az = radians(inp.panel_azimuth_deg)

    cos_theta = (
        cos(zen) * cos(tilt)
        +
        sin(zen) * sin(tilt) * cos(az - panel_az)
    )

    # Evitar contribución negativa
    return max(cos_theta, 0.0)


# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def calcular_irradiancia_plano(inp: IrradianciaInput) -> IrradianciaPlano:
    """
    Calcula irradiancia en el plano del generador (POA).

    Componentes:

        • directa (beam)
        • difusa (cielo)
        • reflejada (suelo)
    """
    
    # ------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------

    if inp.dni < 0 or inp.dhi < 0 or inp.ghi < 0:
        raise ValueError("Irradiancia negativa no válida")

    if not (0 <= inp.albedo <= 1):
        raise ValueError("Albedo fuera de rango [0–1]")

    if inp.solar_zenith_deg < 0 or inp.solar_zenith_deg > 180:
        raise ValueError("Zenith fuera de rango")

    # ------------------------------------------------------
    # PRE-CÁLCULOS
    # ------------------------------------------------------

    cos_theta = _cos_theta_i(inp)
    tilt = radians(inp.panel_tilt_deg)

    # ------------------------------------------------------
    # 1. COMPONENTE DIRECTA
    # ------------------------------------------------------

    if inp.solar_zenith_deg >= 90:
        poa_directa = 0.0
    else:
        poa_directa = inp.dni * cos_theta

    # ------------------------------------------------------
    # 2. COMPONENTE DIFUSA (MODELO ISOTRÓPICO)
    # ------------------------------------------------------

    poa_difusa = inp.dhi * (1 + cos(tilt)) / 2

    # ------------------------------------------------------
    # 3. COMPONENTE REFLEJADA
    # ------------------------------------------------------

    poa_reflejada = inp.ghi * inp.albedo * (1 - cos(tilt)) / 2

    # ------------------------------------------------------
    # 4. TOTAL
    # ------------------------------------------------------

    poa_total = poa_directa + poa_difusa + poa_reflejada

    # Protección física
    poa_total = max(poa_total, 0.0)

    return IrradianciaPlano(
        poa_total=poa_total,
        poa_directa=poa_directa,
        poa_difusa=poa_difusa,
        poa_reflejada=poa_reflejada
    )


# ==========================================================
# ESTRUCTURA DEL DOMINIO
# ==========================================================

"""
Este módulo produce:

IrradianciaPlano


Estructura:

IrradianciaPlano
    ├─ poa_total
    ├─ poa_directa
    ├─ poa_difusa
    └─ poa_reflejada


Flujo de integración:

ResultadoClima
        ↓
posicion_solar
        ↓
calcular_irradiancia_plano
        ↓
EstadoSolarHora
        ↓
energy


Fronteras:

✔ clima → datos
✔ solar → geometría + POA
✔ energy → potencia

Este módulo NO cruza esas fronteras.
"""
