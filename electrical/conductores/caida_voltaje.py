"""
Motor físico de caída de voltaje — FV Engine

FRONTERA DEL MÓDULO
-------------------
Este módulo implementa únicamente el modelo físico resistivo
del conductor.

Responsabilidades:
    - cálculo de caída de tensión
    - lectura de resistencia del conductor
    - ajuste de calibre por criterio de VD

NO realiza:
    - cálculo de ampacidad NEC
    - factores de corrección
    - selección inicial de conductor

Eso pertenece a otros módulos del dominio conductores.
"""

from __future__ import annotations
from typing import Dict, List


# ==========================================================
# MODELO FÍSICO DE CAÍDA DE TENSIÓN
# ==========================================================

def caida_tension_pct(
    *,
    v: float,
    i: float,
    l_m: float,
    r_ohm_km: float,
    n_hilos: int = 2,
) -> float:
    """
    Calcula caída de tensión porcentual usando modelo resistivo.

    Fórmula:

        VD% = 100 * (I * R_total) / V

        R_total = r_ohm_km * (L_km) * n_hilos

    Parámetros
    ----------
    v : tensión del circuito (V)
    i : corriente del circuito (A)
    l_m : longitud del tramo (m)
    r_ohm_km : resistencia del conductor (ohm/km)
    n_hilos : número de conductores en el camino de corriente
              (2 para ida-vuelta en DC)

    Retorna
    -------
    float : caída de tensión en porcentaje
    """

    try:
        v = float(v)
        i = float(i)
        l_m = float(l_m)
        r_ohm_km = float(r_ohm_km)
        n_hilos = int(n_hilos)
    except Exception:
        return 0.0

    if n_hilos < 1:
        n_hilos = 1

    if v <= 0 or i <= 0 or l_m <= 0 or r_ohm_km <= 0:
        return 0.0

    r_total = r_ohm_km * (l_m / 1000.0) * n_hilos

    vd_pct = 100.0 * (i * r_total) / v

    return vd_pct


# ==========================================================
# RESISTENCIA DE CONDUCTOR DESDE TABLA
# ==========================================================

def resistencia_de_tabla(
    tabla: List[Dict[str, float]],
    awg: str,
) -> float:
    """
    Obtiene la resistencia del conductor desde la tabla base.

    Si el calibre no existe retorna 0.0.
    """

    a = str(awg)

    for t in tabla:
        if str(t.get("awg")) == a:
            return float(t.get("r_ohm_km", 0.0))

    return 0.0


# ==========================================================
# AJUSTE DE CALIBRE POR CAÍDA DE VOLTAJE
# ==========================================================

def ajustar_calibre_por_vd(
    tabla: List[Dict[str, float]],
    *,
    awg: str,
    i_a: float,
    v_v: float,
    l_m: float,
    vd_obj_pct: float,
    n_hilos: int = 2,
) -> str:
    """
    Incrementa el calibre del conductor hasta cumplir
    la caída de tensión objetivo.

    Parámetros
    ----------
    tabla : tabla de conductores ordenada por calibre
    awg : calibre inicial
    i_a : corriente del circuito
    v_v : tensión del circuito
    l_m : longitud del tramo
    vd_obj_pct : caída de tensión máxima permitida
    """

    try:
        i_a = float(i_a)
        v_v = float(v_v)
        l_m = float(l_m)
        vd_obj_pct = float(vd_obj_pct)
        n_hilos = int(n_hilos)
    except Exception:
        return str(awg)

    awg = str(awg)

    # buscar posición inicial
    idx0 = next(
        (k for k, t in enumerate(tabla) if str(t.get("awg")) == awg),
        None,
    )

    if idx0 is None:
        idx0 = 0

    idx = idx0

    while idx < len(tabla):

        r = float(tabla[idx].get("r_ohm_km", 0.0))

        vd = caida_tension_pct(
            v=v_v,
            i=i_a,
            l_m=l_m,
            r_ohm_km=r,
            n_hilos=n_hilos,
        )

        if vd <= vd_obj_pct:
            return str(tabla[idx].get("awg"))

        idx += 1

    # si no cumple ni con el mayor calibre
    return str(tabla[-1].get("awg"))
