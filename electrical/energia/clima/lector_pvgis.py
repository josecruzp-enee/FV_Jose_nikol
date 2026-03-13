from __future__ import annotations

"""
LECTOR PVGIS — FV Engine

Responsabilidad
---------------
Descargar datos climáticos horarios desde PVGIS.

Datos obtenidos:
    • GHI (irradiancia horizontal)
    • temperatura ambiente

Salida:
    List[ClimaHora] con 8760 horas.

Fuente:
    https://re.jrc.ec.europa.eu/api/
"""

from typing import List
import requests

from .clima_modelo import ClimaHora


# ==========================================================
# URL BASE PVGIS
# ==========================================================

PVGIS_URL = "https://re.jrc.ec.europa.eu/api/seriescalc"


# ==========================================================
# DESCARGA CLIMA PVGIS
# ==========================================================

def descargar_clima_pvgis(
    lat: float,
    lon: float,
    startyear: int = 2020,
    endyear: int = 2020
) -> List[ClimaHora]:

    params = {

        "lat": lat,
        "lon": lon,

        "outputformat": "json",

        "startyear": startyear,
        "endyear": endyear,

        "usehorizon": 1,

        "pvcalculation": 0,

        "browser": 0
    }

    r = requests.get(PVGIS_URL, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError("Error descargando datos PVGIS")

    data = r.json()

    hourly = data["outputs"]["hourly"]

    clima = []

    for h in hourly:

        ghi = h.get("G(h)", 0)
        temp = h.get("T2m", 25)

        clima.append(
            ClimaHora(
                ghi_wm2=float(ghi),
                temp_amb_c=float(temp)
            )
        )

    return clima
