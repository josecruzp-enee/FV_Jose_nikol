from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO SOLAR — FV Engine

Responsabilidad
---------------
Coordinar los modelos solares del sistema:

• posición del sol
• irradiancia en plano del arreglo (POA)

Entrada:
    EntradaSolar

Salida:
    dict con posición solar y POA
"""

from typing import Dict, Any

from .entrada_solar import EntradaSolar
from .posicion_solar import calcular_posicion_solar
from .irradiancia_plano import calcular_irradiancia_plano


# ==========================================================
# VALIDACIÓN DE ENTRADA
# ==========================================================

def _validar_entrada(e: EntradaSolar):

    errores = []

    if e.lat is None or e.lon is None:
        errores.append("Latitud/longitud no definidas.")

    if e.fecha_hora is None:
        errores.append("fecha_hora no definida.")

    if e.ghi_wm2 is None:
        errores.append("ghi_wm2 no definido.")

    if e.tilt_deg is None:
        errores.append("tilt_deg no definido.")

    if e.azimuth_panel_deg is None:
        errores.append("azimuth_panel_deg no definido.")

    return errores


# ==========================================================
# ORQUESTADOR
# ==========================================================

def ejecutar_solar(
    entrada: EntradaSolar
) -> Dict[str, Any]:

    errores = _validar_entrada(entrada)

    if errores:
        return {
            "ok": False,
            "errores": errores,
            "warnings": []
        }

    warnings = []

    # ------------------------------------------------------
    # POSICIÓN SOLAR
    # ------------------------------------------------------

    try:

        pos = calcular_posicion_solar(
            lat=entrada.lat,
            lon=entrada.lon,
            fecha_hora=entrada.fecha_hora
        )

    except Exception as e:

        return {
            "ok": False,
            "errores": [f"Error en posición solar: {str(e)}"],
            "warnings": warnings
        }

    # ------------------------------------------------------
    # IRRADIANCIA EN PLANO DEL ARREGLO
    # ------------------------------------------------------

    try:

        poa = calcular_irradiancia_plano(
            ghi_wm2=entrada.ghi_wm2,
            zenith_deg=pos["zenith_deg"],
            azimuth_sol_deg=pos["azimuth_deg"],
            tilt_deg=entrada.tilt_deg,
            azimuth_panel_deg=entrada.azimuth_panel_deg
        )

    except Exception as e:

        return {
            "ok": False,
            "errores": [f"Error en irradiancia POA: {str(e)}"],
            "warnings": warnings
        }

    # ------------------------------------------------------
    # RESULTADO CONSOLIDADO
    # ------------------------------------------------------

    return {

        "ok": True,

        "solar_position": pos,

        "poa_wm2": poa,

        "warnings": warnings,

        "meta": {
            "lat": entrada.lat,
            "lon": entrada.lon
        }

    }
