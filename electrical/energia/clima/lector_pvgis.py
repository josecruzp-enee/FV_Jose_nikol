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

    try:
        r = requests.get(PVGIS_URL, params=params, timeout=60)
        r.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Error descargando datos PVGIS: {e}") from e

    data = r.json()

    if "outputs" not in data or "hourly" not in data["outputs"]:
        raise RuntimeError("Formato de respuesta PVGIS inválido")

    hourly = data["outputs"]["hourly"]

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

    if len(clima) != 8760:
        raise RuntimeError(
            f"PVGIS devolvió {len(clima)} horas en lugar de 8760"
        )

    return clima
