from __future__ import annotations

"""
MOTOR FÍSICO DE CAÍDA DE VOLTAJE — FV ENGINE

Calcula caída de tensión y valida cumplimiento.

NO usa dict
SOLO dataclass
"""

from dataclasses import dataclass
from typing import List


# ==========================================================
# MODELO CONDUCTOR
# ==========================================================

@dataclass(frozen=True)
class Conductor:
    awg: str
    r_ohm_km: float


# ==========================================================
# CAÍDA DE TENSIÓN
# ==========================================================

def caida_tension_pct(
    *,
    v: float,
    i: float,
    l_m: float,
    r_ohm_km: float,
    n_hilos: float = 2.0,
) -> float:
    """
    Calcula caída de tensión en porcentaje.
    """

    if v <= 0:
        raise ValueError("Voltaje inválido")

    if i <= 0 or l_m <= 0 or r_ohm_km <= 0:
        return 0.0

    if n_hilos <= 0:
        n_hilos = 1.0

    r_total = r_ohm_km * (l_m / 1000.0) * n_hilos

    vd_pct = 100.0 * (i * r_total) / v

    return vd_pct


# ==========================================================
# AJUSTE DE CALIBRE POR VD
# ==========================================================

def ajustar_calibre_por_vd(
    tabla: List[Conductor],
    *,
    awg: str,
    i_a: float,
    v_v: float,
    l_m: float,
    vd_obj_pct: float,
    n_hilos: float = 2.0,
) -> str:
    """
    Encuentra el calibre mínimo que cumple caída de tensión.
    """

    if not tabla:
        raise ValueError("Tabla de conductores vacía")

    if v_v <= 0:
        raise ValueError("Voltaje inválido")

    if vd_obj_pct <= 0:
        raise ValueError("vd_obj_pct inválido")

    # Buscar índice inicial
    idx0 = next(
        (k for k, t in enumerate(tabla) if t.awg == str(awg)),
        0,
    )

    for t in tabla[idx0:]:

        vd = caida_tension_pct(
            v=v_v,
            i=i_a,
            l_m=l_m,
            r_ohm_km=t.r_ohm_km,
            n_hilos=n_hilos,
        )

        if vd <= vd_obj_pct:
            return t.awg

    # Si ninguno cumple → mayor calibre disponible
    return tabla[-1].awg


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# FUNCIONES:
# ----------------------------------------------------------
# caida_tension_pct(...)
# ajustar_calibre_por_vd(...)
#
#
# ----------------------------------------------------------
# ENTRADA
# ----------------------------------------------------------
#
# v: float
#     → voltaje del circuito
#
# i: float
#     → corriente del circuito
#
# l_m: float
#     → longitud del conductor
#
# r_ohm_km: float
#     → resistencia del conductor
#
# n_hilos: float
#     → camino eléctrico (2 DC, 1.732 trifásico)
#
#
# ----------------------------------------------------------
# PROCESO
# ----------------------------------------------------------
#
# r_total = r * longitud * factor_camino
#
# vd = (I × R) / V
#
#
# ----------------------------------------------------------
# SALIDA
# ----------------------------------------------------------
#
# vd_pct:
#     → caída de tensión [%]
#
# awg_resultado:
#     → calibre que cumple VD objetivo
#
#
# ----------------------------------------------------------
# USO EN FV ENGINE
# ----------------------------------------------------------
#
# Corrientes
#       ↓
# tramo_conductor
#       ↓
# ajuste VD (este módulo)
#
#
# ----------------------------------------------------------
# PRINCIPIO
# ----------------------------------------------------------
#
# Este módulo NO selecciona conductor final.
#
# SOLO valida:
#
#   "¿Este calibre cumple VD?"
#
# ==========================================================
