from __future__ import annotations

"""
LECTOR PVGIS — FV Engine

Responsabilidad
---------------
Descargar datos climáticos horarios desde la API de PVGIS
y convertirlos al modelo interno del dominio clima.

Salida
------
ResultadoClima con 8760 horas válidas.
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
        "browser": 0,
    }

    # ------------------------------------------------------
    # DESCARGA
    # ------------------------------------------------------

    try:
        r = requests.get(PVGIS_URL, params=params, timeout=60)
        r.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Error descargando datos PVGIS: {e}") from e

    # ------------------------------------------------------
    # VALIDAR RESPUESTA
    # ------------------------------------------------------

    data = r.json()

    if "outputs" not in data or "hourly" not in data["outputs"]:
        raise RuntimeError("Formato de respuesta PVGIS inválido")

    hourly = data["outputs"]["hourly"]

    # ------------------------------------------------------
    # CONSTRUIR SERIE CLIMÁTICA
    # ------------------------------------------------------

    horas: list[ClimaHora] = []

    for h in hourly:

        # ----------------------------------------
        # TIMESTAMP
        # ----------------------------------------
        try:
            timestamp = datetime.strptime(
                h["time"],
                "%Y%m%d:%H%M"
            )
        except Exception:
            raise RuntimeError(f"Error parseando timestamp: {h.get('time')}")

        # ----------------------------------------
        # IRRADIANCIA (ROBUSTA)
        # ----------------------------------------
        ghi = float(
            h.get("G(h)") or
            h.get("G(i)") or
            0
        )

        dni = float(
            h.get("Gb(n)") or
            h.get("Gb(i)") or
            0
        )

        dhi = float(
            h.get("Gd(h)") or
            h.get("Gd(i)") or
            0
        )

        # ----------------------------------------
        # VALIDACIÓN LOCAL
        # ----------------------------------------
        if ghi < 0 or dni < 0 or dhi < 0:
            raise RuntimeError("Irradiancia negativa detectada en PVGIS")

        # ----------------------------------------
        # TEMPERATURA Y VIENTO
        # ----------------------------------------
        temp = float(h.get("T2m", 25) or 25)
        viento = float(h.get("WS10m", 1.0) or 1.0)

        # ----------------------------------------
        # CREAR OBJETO
        # ----------------------------------------
        horas.append(
            ClimaHora(
                timestamp=timestamp,
                ghi_wm2=ghi,
                dni_wm2=dni,
                dhi_wm2=dhi,
                temp_amb_c=temp,
                viento_ms=viento,
            )
        )

    # ------------------------------------------------------
    # VALIDACIÓN GLOBAL
    # ------------------------------------------------------

    if len(horas) != 8760:
        raise RuntimeError(
            f"PVGIS devolvió {len(horas)} horas en lugar de 8760"
        )

    ghi_total = sum(h.ghi_wm2 for h in horas)

    if ghi_total <= 0:
        raise RuntimeError("PVGIS devolvió irradiancia total = 0")

    # ------------------------------------------------------
    # RESULTADO FINAL
    # ------------------------------------------------------

    return ResultadoClima(
        latitud=entrada.lat,
        longitud=entrada.lon,
        horas=horas,
        fuente="PVGIS",
        meta={
            "startyear": entrada.startyear,
            "endyear": entrada.endyear,
            "n_horas": len(horas),
        }
    )
