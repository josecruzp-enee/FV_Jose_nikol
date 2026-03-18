from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import requests
import streamlit as st

from .resultado_clima import ResultadoClima, ClimaHora


# ==========================================================
# MODELO DE ENTRADA
# ==========================================================

@dataclass
class EntradaClimaPVGIS:
    lat: float
    lon: float
    startyear: int = 2019   # ✔ año no bisiesto
    endyear: int = 2019


# ==========================================================
# URL BASE
# ==========================================================

PVGIS_URL = "https://re.jrc.ec.europa.eu/api/seriescalc"


# ==========================================================
# MAPEO ROBUSTO
# ==========================================================

def _mapear_radiacion(h: dict) -> tuple[float, float, float]:

    # --- GHI ---
    ghi = h.get("G(h)")
    if ghi is None:
        ghi = h.get("G(i)", 0.0)

    # --- DNI ---
    dni = h.get("Gb(n)", 0.0)

    # --- DHI ---
    dhi = h.get("Gd(h)", 0.0)

    # --- fallback mínimo ---
    if ghi == 0 and dni > 0:
        ghi = dni * 0.7

    if dhi == 0 and ghi > 0:
        dhi = ghi * 0.2

    return float(ghi), float(dni), float(dhi)


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def descargar_clima_pvgis(
    entrada: EntradaClimaPVGIS
) -> ResultadoClima:

    st.write("🌍 Descargando clima desde PVGIS...")
    st.write(f"📍 Lat: {entrada.lat}, Lon: {entrada.lon}")
    st.write(f"📅 Año: {entrada.startyear}")

    # ------------------------------------------------------
    # VALIDACIÓN ENTRADA
    # ------------------------------------------------------

    if not (-90 <= entrada.lat <= 90):
        raise ValueError(f"Latitud inválida: {entrada.lat}")

    if not (-180 <= entrada.lon <= 180):
        raise ValueError(f"Longitud inválida: {entrada.lon}")

    # ------------------------------------------------------
    # PARAMS
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

    st.write("📡 Enviando request a PVGIS...")
    st.json(params)

    # ------------------------------------------------------
    # REQUEST
    # ------------------------------------------------------

    try:
        r = requests.get(PVGIS_URL, params=params, timeout=60)

        st.write("📥 Status code:", r.status_code)

        if r.status_code != 200:
            st.error("❌ Error en PVGIS")
            st.text(r.text)
            r.raise_for_status()

    except requests.RequestException as e:
        raise RuntimeError(f"Error descargando datos PVGIS: {e}") from e

    data = r.json()

    # ------------------------------------------------------
    # VALIDAR RESPUESTA
    # ------------------------------------------------------

    if "outputs" not in data or "hourly" not in data["outputs"]:
        st.error("❌ Respuesta inválida de PVGIS")
        st.json(data)
        raise RuntimeError("Formato de respuesta PVGIS inválido")

    hourly = data["outputs"]["hourly"]

    st.write("📊 Primer registro PVGIS:")
    st.json(hourly[0])

    if not hourly:
        raise RuntimeError("PVGIS devolvió lista vacía")

    # ------------------------------------------------------
    # CONSTRUIR CLIMA
    # ------------------------------------------------------

    horas: list[ClimaHora] = []

    for h in hourly:

        try:
            timestamp = datetime.strptime(h["time"], "%Y%m%d:%H%M")
        except Exception:
            raise RuntimeError(f"Error parseando timestamp: {h.get('time')}")

        # 🔥 CORRECCIÓN CLAVE
        ghi, dni, dhi = _mapear_radiacion(h)

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
    dni_total = sum(h.dni_wm2 for h in horas)

    st.write("📈 VALIDACIÓN GLOBAL")
    st.write(f"Horas: {n}")
    st.write(f"GHI total: {round(ghi_total, 2)}")
    st.write(f"DNI total: {round(dni_total, 2)}")

    if n != 8760:
        raise RuntimeError(f"PVGIS devolvió {n} horas en lugar de 8760")

    if ghi_total <= 0:
        raise RuntimeError("PVGIS devolvió GHI total = 0")

    if dni_total <= 0:
        raise RuntimeError("PVGIS devolvió DNI total = 0")

    st.success("✅ Clima PVGIS válido")

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
            "n_horas": n,
        }
    )
