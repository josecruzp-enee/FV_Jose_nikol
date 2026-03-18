from __future__ import annotations

"""
CONTRATO DE ENTRADA — DOMINIO SOLAR (UNITARIO)
==============================================

Define la estructura de entrada para el cálculo solar
en una única hora.

Pipeline representado:

    clima (irradiancia + temperatura)
            ↓
    posición solar
            ↓
    irradiancia en plano (POA)

Este contrato es utilizado por:

    ejecutar_solar_unitario.py

NO se utiliza en simulación 8760 directa.
"""

from dataclasses import dataclass
from datetime import datetime


# ==========================================================
# ENTRADA DEL DOMINIO SOLAR
# ==========================================================

@dataclass(frozen=True)
class EntradaSolar:
    """
    Entrada del modelo solar para una hora específica.
    """

    # ------------------------------------------------------
    # UBICACIÓN
    # ------------------------------------------------------

    lat: float
    # Latitud del sitio [°]

    lon: float
    # Longitud del sitio [°]

    # ------------------------------------------------------
    # TIEMPO
    # ------------------------------------------------------

    fecha_hora: datetime
    # Timestamp de la simulación

    # ------------------------------------------------------
    # IRRADIANCIA (desde clima)
    # ------------------------------------------------------

    ghi_wm2: float
    # Global Horizontal Irradiance

    dni_wm2: float
    # Direct Normal Irradiance

    dhi_wm2: float
    # Diffuse Horizontal Irradiance

    # ------------------------------------------------------
    # TEMPERATURA (desde clima)
    # ------------------------------------------------------

    temp_amb_c: float
    # Temperatura ambiente [°C]
    #
    # Importante para modelos térmicos posteriores.

    # ------------------------------------------------------
    # GEOMETRÍA DEL GENERADOR
    # ------------------------------------------------------

    tilt_deg: float
    # Inclinación del panel [°]

    azimuth_panel_deg: float
    # Azimut del panel [°]
    #
    # Convención:
    #   180° → Sur (hemisferio norte)
    #   0°   → Norte
    #   90°  → Este
    #   270° → Oeste


# ==========================================================
# ESTRUCTURA DEL DOMINIO
# ==========================================================

"""
Este contrato representa:

EntradaSolar
    ├─ ubicación (lat, lon)
    ├─ tiempo (timestamp)
    ├─ irradiancia (GHI, DNI, DHI)
    ├─ temperatura (ambiente)
    └─ geometría del panel


Flujo de integración:

ResultadoClima (1 hora)
        ↓
EntradaSolar
        ↓
ejecutar_solar_unitario
        ↓
SolarResultado


Fronteras:

✔ clima → provee irradiancia + temperatura
✔ solar → transforma irradiancia → POA
✔ energy → usa POA para potencia

Este contrato NO cruza esas fronteras.
"""
