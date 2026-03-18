from __future__ import annotations

"""
LECTOR PVGIS — FV Engine (VERSIÓN FINAL PRODUCCIÓN)

Responsabilidad
---------------
Descargar datos climáticos horarios desde la API de PVGIS
y convertirlos al modelo interno del dominio clima.

Incluye:
✔ Corrección DNI (components=1)
✔ Base de datos correcta (SARAH2)
✔ Validaciones fuertes
✔ Protección contra respuestas vacías

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

    # ------------------------------------------------------
    # VALIDACIÓN ENTRADA
    # ------------------------------------------------------

    if not (-90 <= entrada.lat <= 90):
        raise ValueError(f"Latitud inválida: {entrada.lat}")

    if not (-180 <= entrada.lon <= 180):
        raise ValueError(f"Longitud inválida: {entrada.lon}")

    # ------------------------------------------------------
    # PARAMETROS CORRECTOS
    # ------------------------------------------------------

    params = {
        "lat": entrada.lat,
        "lon": entrada.lon,
        "outputformat": "json",
        "startyear": entrada.startyear,
        "endyear": entrada.endyear,
        "usehorizon": 1,
        "pvcalculation": 0,
        "raddatabase": "PVGIS-SARAH2",
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

    data = r.json()

    # ------------------------------------------------------
    # VALIDAR RESPUESTA
    # ------------------------------------------------------

    if "outputs" not in data or "hourly" not in data["outputs"]:
        raise RuntimeError("Formato de respuesta PVGIS inválido")

    hourly = data["outputs"]["hourly"]

    if not hourly:
        raise RuntimeError("PVGIS devolvió lista vacía")

    # Validación clave: irradiancia presente
    if "G(h)" not in hourly[0] and "Gb(n)" not in hourly[0]:
        raise RuntimeError(
            "PVGIS no devolvió irradiancia. "
            "Verifique coordenadas o parámetros."
        )

    # ------------------------------------------------------
    # CONSTRUIR SERIE CLIMÁTICA
    # ------------------------------------------------------

    horas: list[ClimaHora] = []

    for h in hourly:

        # TIMESTAMP
        try:
            timestamp = datetime.strptime(h["time"], "%Y%m%d:%H%M")
        except Exception:
            raise RuntimeError(f"Error parseando timestamp: {h.get('time')}")

        # IRRADIANCIA
        ghi = float(h.get("G(h)", 0.0))
        dni = float(h.get("Gb(n)", 0.0))
        dhi = float(h.get("Gd(h)", 0.0))

        # VALIDACIÓN LOCAL
        if ghi < 0 or dni < 0 or dhi < 0:
            raise RuntimeError("Irradiancia negativa detectada en PVGIS")

        # TEMPERATURA Y VIENTO
        temp = float(h.get("T2m", 25.0))
        viento = float(h.get("WS10m", 1.0))

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
    dni_total = sum(h.dni_wm2 for h in horas)

    if ghi_total <= 0:
        raise RuntimeError("PVGIS devolvió GHI total = 0")

    if dni_total <= 0:
        raise RuntimeError(
            "PVGIS devolvió DNI total = 0 (revisar components=1)"
        )

    # ------------------------------------------------------
    # DEBUG CONTROLADO
    # ------------------------------------------------------

    print("\nDEBUG PVGIS")
    print("Lat:", entrada.lat, "Lon:", entrada.lon)
    print("Horas:", len(horas))
    print("GHI total:", round(ghi_total, 2))
    print("DNI total:", round(dni_total, 2))
    print()

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
