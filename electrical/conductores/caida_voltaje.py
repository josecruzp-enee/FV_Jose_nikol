from __future__ import annotations

"""
MOTOR FÍSICO DE CAÍDA DE VOLTAJE — FV ENGINE

Calcula caída de tensión y valida cumplimiento.

✔ NO usa dict
✔ USA modelo unificado (Conductor)
"""

from typing import List

# 🔥 IMPORTANTE: modelo único
from .tablas_conductores import Conductor


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
