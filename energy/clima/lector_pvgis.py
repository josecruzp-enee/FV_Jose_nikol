from __future__ import annotations

"""
LECTOR PVGIS — DOMINIO CLIMA (FV Engine)
========================================

Responsabilidad
---------------

Descargar datos climáticos horarios desde PVGIS y convertirlos
al contrato interno del dominio clima (ResultadoClima).

Pipeline representado:

    PVGIS API
        ↓
    parsing JSON
        ↓
    normalización de variables
        ↓
    construcción de ClimaHora
        ↓
    ResultadoClima

Frontera del módulo
-------------------

Entrada:
    EntradaClimaPVGIS

Salida:
    ResultadoClima

Dependencias:
    • requests (infraestructura)
    • resultado_clima (dominio)

Reglas arquitectónicas
----------------------

    ✔ Este módulo pertenece a infraestructura de clima
    ✔ Devuelve objetos del dominio (ResultadoClima)
    ❌ No contiene lógica solar
    ❌ No contiene lógica energética
    ❌ No depende de UI (streamlit)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple, List

import requests

from .resultado_clima import ResultadoClima, ClimaHora


# ==========================================================
# MODELO DE ENTRADA
# ==========================================================

@dataclass
class EntradaClimaPVGIS:
    """
    Parámetros de consulta a PVGIS.
    """

    lat: float
    lon: float
    startyear: int = 2019   # año no bisiesto recomendado
    endyear: int = 2019


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

PVGIS_URL = "https://re.jrc.ec.europa.eu/api/seriescalc"


# ==========================================================
# MAPEO DE RADIACIÓN
# ==========================================================
import math
from typing import Tuple

def _mapear_radiacion(h: dict, zenith_deg: float) -> Tuple[float, float, float]:
    """
    Mapeo PVGIS → (GHI, DNI, DHI) con reconstrucción física robusta.

    Nivel: PRO (tipo PVsyst simplificado)

    - Usa zenith real
    - Reconstruye DNI correctamente
    - Maneja casos límite (noche, horizonte)
    """

    # --------------------------------------------------
    # GHI
    # --------------------------------------------------
    ghi = h.get("G(h)")
    if ghi is None:
        ghi = h.get("G(i)", 0.0)

    # --------------------------------------------------
    # DHI
    # --------------------------------------------------
    dhi = h.get("Gd(h)", 0.0)

    # --------------------------------------------------
    # DNI directo (si existe)
    # --------------------------------------------------
    dni = (
        h.get("Gb(n)") or
        h.get("Gb(i)") or
        h.get("G(b)")
    )

    # --------------------------------------------------
    # GEOMETRÍA SOLAR
    # --------------------------------------------------
    zenith_rad = math.radians(zenith_deg)
    cos_zen = math.cos(zenith_rad)

    # --------------------------------------------------
    # RECONSTRUCCIÓN DNI (FÍSICA REAL)
    # --------------------------------------------------
    if dni is None:

        if ghi > 0 and dhi >= 0 and cos_zen > 0.065:
            # 0.065 ≈ zenith < 86° (evita explosiones cerca del horizonte)
            dni = (ghi - dhi) / cos_zen
            dni = max(dni, 0.0)
        else:
            dni = 0.0

    # --------------------------------------------------
    # LIMPIEZA FÍSICA
    # --------------------------------------------------

    # Noche → todo cero
    if zenith_deg >= 90:
        return 0.0, 0.0, 0.0

    # Evitar valores absurdos
    dni = min(dni, 1400)   # límite físico razonable
    ghi = max(ghi, 0.0)
    dhi = max(dhi, 0.0)

    # Corrección consistencia básica
    if dhi > ghi:
        dhi = ghi

    return float(ghi), float(dni), float(dhi)


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def descargar_clima_pvgis(
    entrada: EntradaClimaPVGIS
) -> ResultadoClima:
    """
    Descarga y construye un ResultadoClima desde PVGIS.

    Parámetros
    ----------
    entrada:
        Coordenadas y rango temporal

    Retorna
    -------
    ResultadoClima validado estructuralmente
    """

    # ------------------------------------------------------
    # VALIDACIÓN DE ENTRADA
    # ------------------------------------------------------

    if not (-90 <= entrada.lat <= 90):
        raise ValueError(f"Latitud inválida: {entrada.lat}")

    if not (-180 <= entrada.lon <= 180):
        raise ValueError(f"Longitud inválida: {entrada.lon}")

    # ------------------------------------------------------
    # PARAMETROS PVGIS
    # ------------------------------------------------------

    params = {
        "lat": entrada.lat,
        "lon": entrada.lon,
        "outputformat": "json",
        "startyear": entrada.startyear,
        "endyear": entrada.endyear,
        "usehorizon": 1,
        "pvcalculation": 0,
        "angle": 0,
        "aspect": 0,
    }

    # ------------------------------------------------------
    # REQUEST
    # ------------------------------------------------------

    try:
        r = requests.get(PVGIS_URL, params=params, timeout=60)

        if r.status_code != 200:
            raise RuntimeError(f"Error PVGIS: {r.status_code} - {r.text}")

    except requests.RequestException as e:
        raise RuntimeError(f"Error descargando PVGIS: {e}") from e

    data = r.json()

    # ------------------------------------------------------
    # VALIDACIÓN RESPUESTA
    # ------------------------------------------------------

    if "outputs" not in data or "hourly" not in data["outputs"]:
        raise RuntimeError("Formato de respuesta PVGIS inválido")

    hourly = data["outputs"]["hourly"]

    if not hourly:
        raise RuntimeError("PVGIS devolvió lista vacía")

    # ------------------------------------------------------
    # CONSTRUCCIÓN DEL CLIMA
    # ------------------------------------------------------

    horas: List[ClimaHora] = []

    for h in hourly:

        try:
            timestamp = datetime.strptime(h["time"], "%Y%m%d:%H%M")
        except Exception:
            raise RuntimeError(f"Timestamp inválido: {h.get('time')}")

        ghi, dni, dhi = _mapear_radiacion(h, solar.zenith_deg)

        if ghi < 0 or dni < 0 or dhi < 0:
            raise RuntimeError("Irradiancia negativa detectada")

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

    n = len(horas)
    ghi_total = sum(h.ghi_wm2 for h in horas)

    if n != 8760:
        raise RuntimeError(f"Se esperaban 8760 horas, se obtuvieron {n}")

    if ghi_total <= 0:
        raise RuntimeError("Clima inválido: GHI total = 0")

    # ------------------------------------------------------
    # SALIDA
    # ------------------------------------------------------

    return ResultadoClima(
        latitud=entrada.lat,
        longitud=entrada.lon,
        horas=horas,
        fuente="PVGIS",
        meta={
            "startyear": entrada.startyear,
            "endyear": entrada.endyear,
            "n_horas": n,
        }
    )

"""
ResultadoClima
    ├─ latitud
    ├─ longitud
    │
    ├─ horas (8760)
    │      ├─ timestamp
    │      ├─ ghi_wm2
    │      ├─ dni_wm2
    │      ├─ dhi_wm2
    │      ├─ temp_amb_c
    │      └─ viento_ms
    │
    ├─ fuente
    └─ meta
"""
