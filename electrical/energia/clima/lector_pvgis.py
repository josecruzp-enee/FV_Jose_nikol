from __future__ import annotations

"""
LECTOR PVGIS — FV Engine

Responsabilidad
---------------
Descargar datos climáticos horarios desde PVGIS.

Este módulo representa la frontera entre:

    API PVGIS
        ↓
    Dominio clima de FV Engine

Salida
------
ResultadoClima
"""

from dataclasses import dataclass
from datetime import datetime
import requests

from .resultado_clima import ResultadoClima, ClimaHora


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
# URL BASE PVGIS
# ==========================================================

PVGIS_URL = "https://re.jrc.ec.europa.eu/api/seriescalc"


# ==========================================================
# DESCARGA CLIMA PVGIS
# ==========================================================

def descargar_clima_pvgis(
    entrada: EntradaClimaPVGIS
) -> ResultadoClima:

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
    # DESCARGA
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
    # CONSTRUIR SERIE CLIMÁTICA
    # ------------------------------------------------------

    horas = []

    for h in hourly:

        # tiempo PVGIS
        timestamp = datetime.strptime(
            h["time"],
            "%Y%m%d:%H%M"
        )

        ghi = float(h.get("G(h)", 0))

        temp = float(h.get("T2m", 25))


        horas.append(

            ClimaHora(

                timestamp=timestamp,

                ghi_wm2=ghi,

                temp_amb_c=temp

            )

        )


    # ------------------------------------------------------
    # VALIDAR 8760 HORAS
    # ------------------------------------------------------

    if len(horas) != 8760:

        raise RuntimeError(

            f"PVGIS devolvió {len(horas)} horas en lugar de 8760"

        )


    # ------------------------------------------------------
    # RESULTADO
    # ------------------------------------------------------

    return ResultadoClima(

        horas=horas,

        latitud=entrada.lat,

        longitud=entrada.lon,

        fuente="PVGIS",

        meta={

            "startyear": entrada.startyear,
            "endyear": entrada.endyear

        }

    )
