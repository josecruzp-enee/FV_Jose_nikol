from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO SOLAR (MODO UNITARIO) — FV Engine
========================================================

Responsabilidad
---------------

Calcular el estado solar para una única hora.

Pipeline representado:

    clima (GHI, DNI, DHI)
            ↓
    posición solar
            ↓
    irradiancia en plano (POA)
            ↓
    SolarResultado

Uso principal
-------------

    ✔ pruebas unitarias
    ✔ validación de modelos
    ✔ simulaciones puntuales

Para simulación anual usar:

    simulacion_8760.py

Frontera del dominio
--------------------

Entrada:
    EntradaSolar

Salida:
    SolarResultado

Este módulo NO calcula energía.
"""

from dataclasses import dataclass

from .entrada_solar import EntradaSolar
from .posicion_solar import calcular_posicion_solar, SolarInput
from .irradiancia_plano import calcular_irradiancia_plano, IrradianciaInput


# ==========================================================
# SALIDA DEL DOMINIO SOLAR
# ==========================================================

@dataclass(frozen=True)
class SolarResultado:
    """
    Resultado solar para una hora específica.
    """

    # ------------------------------------------------------
    # IRRADIANCIA
    # ------------------------------------------------------

    poa_total_wm2: float
    poa_directa_wm2: float
    poa_difusa_wm2: float
    poa_reflejada_wm2: float

    # ------------------------------------------------------
    # GEOMETRÍA
    # ------------------------------------------------------

    zenith_deg: float
    azimuth_deg: float


# ==========================================================
# VALIDACIÓN
# ==========================================================

def _validar(e: EntradaSolar):
    """
    Valida consistencia de entrada solar.
    """

    if e.lat is None or e.lon is None:
        raise ValueError("Lat/lon inválidos")

    if e.fecha_hora is None:
        raise ValueError("fecha_hora requerida")

    if e.dni_wm2 < 0 or e.dhi_wm2 < 0 or e.ghi_wm2 < 0:
        raise ValueError("Irradiancia negativa")

    if e.tilt_deg is None or e.azimuth_panel_deg is None:
        raise ValueError("Geometría inválida")


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================

def ejecutar_solar_unitario(entrada: EntradaSolar) -> SolarResultado:
    """
    Ejecuta el modelo solar para una hora.

    Flujo:

        1) Validación
        2) Posición solar
        3) POA
        4) Construcción resultado
    """

    _validar(entrada)

    # ------------------------------------------------------
    # 1. POSICIÓN SOLAR
    # ------------------------------------------------------

    pos = calcular_posicion_solar(
        SolarInput(
            latitud_deg=entrada.lat,
            longitud_deg=entrada.lon,
            fecha_hora=entrada.fecha_hora
        )
    )

    # ------------------------------------------------------
    # 2. IRRADIANCIA EN PLANO
    # ------------------------------------------------------

    irr = calcular_irradiancia_plano(
        IrradianciaInput(
            dni=entrada.dni_wm2,
            dhi=entrada.dhi_wm2,
            ghi=entrada.ghi_wm2,
            solar_zenith_deg=pos.zenith_deg,
            solar_azimuth_deg=pos.azimuth_deg,
            panel_tilt_deg=entrada.tilt_deg,
            panel_azimuth_deg=entrada.azimuth_panel_deg
        )
    )

    # ------------------------------------------------------
    # 3. RESULTADO
    # ------------------------------------------------------

    return SolarResultado(
        poa_total_wm2=irr.poa_total,
        poa_directa_wm2=irr.poa_directa,
        poa_difusa_wm2=irr.poa_difusa,
        poa_reflejada_wm2=irr.poa_reflejada,
        zenith_deg=pos.zenith_deg,
        azimuth_deg=pos.azimuth_deg
    )


# ==========================================================
# ESTRUCTURA DEL DOMINIO
# ==========================================================

"""
Este módulo produce:

SolarResultado


Estructura:

SolarResultado
    ├─ poa_total_wm2
    ├─ poa_directa_wm2
    ├─ poa_difusa_wm2
    ├─ poa_reflejada_wm2
    │
    ├─ zenith_deg
    └─ azimuth_deg


Flujo de integración:

ResultadoClima (1 hora)
        ↓
ejecutar_solar_unitario
        ↓
SolarResultado
        ↓
(simulación 8760 / energy)


Fronteras:

✔ clima → datos
✔ solar → transformación física
✔ energy → potencia

Este módulo NO cruza esas fronteras.
"""
    if e.lat is None or e.lon is None:
        raise ValueError("Lat/lon inválidos")

    if e.fecha_hora is None:
        raise ValueError("fecha_hora requerida")

    if e.dni_wm2 < 0 or e.dhi_wm2 < 0 or e.ghi_wm2 < 0:
        raise ValueError("Irradiancia negativa")

    if e.tilt_deg is None or e.azimuth_panel_deg is None:
        raise ValueError("Geometría inválida")


# ==========================================================
# ORQUESTADOR
# ==========================================================

def ejecutar_solar(entrada: EntradaSolar) -> SolarResultado:

    _validar(entrada)

    # ------------------------------------------------------
    # POSICIÓN SOLAR
    # ------------------------------------------------------

    pos = calcular_posicion_solar(
        SolarInput(
            latitud_deg=entrada.lat,
            longitud_deg=entrada.lon,
            fecha_hora=entrada.fecha_hora
        )
    )

    # ------------------------------------------------------
    # IRRADIANCIA EN PLANO
    # ------------------------------------------------------

    irr = calcular_irradiancia_plano(
        IrradianciaInput(
            dni=entrada.dni_wm2,
            dhi=entrada.dhi_wm2,
            ghi=entrada.ghi_wm2,
            solar_zenith_deg=pos.zenith_deg,
            solar_azimuth_deg=pos.azimuth_deg,
            panel_tilt_deg=entrada.tilt_deg,
            panel_azimuth_deg=entrada.azimuth_panel_deg
        )
    )

    # ------------------------------------------------------
    # RESULTADO
    # ------------------------------------------------------

    return SolarResultado(
        poa_wm2=irr.poa_total,
        zenith_deg=pos.zenith_deg,
        azimuth_deg=pos.azimuth_deg
    )
