from __future__ import annotations

"""
LECTOR PVGIS — FV Engine

Responsabilidad
---------------
Descargar datos climáticos horarios desde PVGIS.

Este módulo representa la frontera entre:
    API PVGIS  →  Motor FV Engine

Datos obtenidos:
    • GHI  (irradiancia horizontal)
    • DNI  (irradiancia directa)
    • DHI  (irradiancia difusa)
    • Temperatura ambiente

Salida:
    List[ClimaHora] con 8760 horas climáticas.

Fuente:
    https://re.jrc.ec.europa.eu/api/
"""

from dataclasses import dataclass
from typing import List
import requests


# ==========================================================
# MODELO DE ENTRADA
# ==========================================================

@dataclass
class EntradaClimaPVGIS:
    """
    Parámetros necesarios para descargar clima desde PVGIS.
    """

    lat: float
    lon: float

    startyear: int = 2020
    endyear: int = 2020


# ==========================================================
# MODELO DE SALIDA
# ==========================================================

@dataclass
class ClimaHora:
    """
    Representa las condiciones climáticas de una hora.
    """

    tiempo: str

    ghi_wm2: float
    dni_wm2: float
    dhi_wm2: float

    temp_amb_c: float


# ==========================================================
# URL BASE PVGIS
# ==========================================================

PVGIS_URL = "https://re.jrc.ec.europa.eu/api/seriescalc"


# ==========================================================
# DESCARGA CLIMA PVGIS
# ==========================================================

def descargar_clima_pvgis(
    entrada: EntradaClimaPVGIS
) -> List[ClimaHora]:

    params = {

        "lat": entrada.lat,
        "lon": entrada.lon,

        "outputformat": "json",

        "startyear": entrada.startyear,
        "endyear": entrada.endyear,

        "usehorizon": 1,

        "pvcalculation": 0,

        "browser": 0
    }

    # ------------------------------------------------------
    # DESCARGA DATOS
    # ------------------------------------------------------

    try:

        r = requests.get(PVGIS_URL, params=params, timeout=60)

        r.raise_for_status()

    except requests.RequestException as e:

        raise RuntimeError(
            f"Error descargando datos PVGIS: {e}"
        ) from e


    # ------------------------------------------------------
    # VALIDAR RESPUESTA
    # ------------------------------------------------------

    data = r.json()

    if "outputs" not in data or "hourly" not in data["outputs"]:

        raise RuntimeError(
            "Formato de respuesta PVGIS inválido"
        )

    hourly = data["outputs"]["hourly"]


    # ------------------------------------------------------
    # CONSTRUIR MODELO CLIMÁTICO
    # ------------------------------------------------------

    clima: List[ClimaHora] = []

    for h in hourly:

        ghi = float(h.get("G(h)", 0) or 0)

        dni = float(h.get("Gb(n)", 0) or 0)

        dhi = float(h.get("Gd(h)", 0) or 0)

        temp = float(h.get("T2m", 25) or 25)

        tiempo = h.get("time")

        clima.append(

            ClimaHora(

                tiempo=tiempo,

                ghi_wm2=ghi,

                dni_wm2=dni,

                dhi_wm2=dhi,

                temp_amb_c=temp
            )

        )


    # ------------------------------------------------------
    # VALIDAR 8760 HORAS
    # ------------------------------------------------------

    if len(clima) != 8760:

        raise RuntimeError(

            f"PVGIS devolvió {len(clima)} horas en lugar de 8760"

        )


    return clima
