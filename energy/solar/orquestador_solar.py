from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO SOLAR — FV ENGINE

Responsabilidad:
    - Calcular irradiancia en plano (POA) para una condición dada

Rol en arquitectura:
    - Componente físico dentro del pipeline 8760
    - NO es endpoint
    - NO tiene modo unitario de uso externo

Flujo:

    clima → solar → energy
"""

from dataclasses import dataclass

from .entrada_solar import EntradaSolar
from .posicion_solar import calcular_posicion_solar, SolarInput
from .irradiancia_plano import calcular_irradiancia_plano, IrradianciaInput


# ==========================================================
# SALIDA
# ==========================================================

@dataclass(frozen=True)
class SolarResultado:
    """
    Resultado solar (estado físico en un instante).
    """

    # Irradiancia
    poa_total_wm2: float
    poa_directa_wm2: float
    poa_difusa_wm2: float
    poa_reflejada_wm2: float

    # Geometría solar
    zenith_deg: float
    azimuth_deg: float


# ==========================================================
# VALIDACIÓN
# ==========================================================

def _validar(e: EntradaSolar) -> None:
    """
    Valida consistencia de la entrada solar.
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
    """
    Ejecuta el modelo solar (componente físico).

    Este método será llamado dentro del loop 8760,
    no directamente por UI.
    """

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
    # IRRADIANCIA EN PLANO (POA)
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
        poa_total_wm2=irr.poa_total,
        poa_directa_wm2=irr.poa_directa,
        poa_difusa_wm2=irr.poa_difusa,
        poa_reflejada_wm2=irr.poa_reflejada,
        zenith_deg=pos.zenith_deg,
        azimuth_deg=pos.azimuth_deg
    )
