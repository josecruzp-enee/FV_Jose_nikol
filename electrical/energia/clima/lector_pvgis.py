from __future__ import annotations

from typing import List
import requests

from .clima_modelo import ClimaHora


PVGIS_URL = "https://re.jrc.ec.europa.eu/api/seriescalc"


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
        dni = h.get("Gb(n)", 0)
        dhi = h.get("Gd(h)", 0)

        temp = h.get("T2m", 25)

        tiempo = h.get("time")

        clima.append(
            ClimaHora(
                tiempo=tiempo,
                ghi_wm2=float(ghi),
                dni_wm2=float(dni),
                dhi_wm2=float(dhi),
                temp_amb_c=float(temp)
            )
        )

    if len(clima) != 8760:
        raise RuntimeError(
            f"PVGIS devolvió {len(clima)} horas en lugar de 8760"
        )

    return clima
