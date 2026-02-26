"""
Modelo físico del tramo — FV Engine.

Responsabilidad:
- Cálculo de caída de tensión (VD) con resistencia DC referencial.
- Utilidades físicas sobre tablas (sin NEC, sin selección por ampacidad).
"""

from __future__ import annotations

from typing import Dict, List


# Calcula la caída de tensión porcentual en un tramo para una corriente dada.
def caida_tension_pct(
    *,
    v: float,
    i: float,
    l_m: float,
    r_ohm_km: float,
    n_hilos: int = 2,
) -> float:
    if v <= 0 or i <= 0 or l_m <= 0 or r_ohm_km <= 0:
        return 0.0

    r_total = float(r_ohm_km) * (float(l_m) / 1000.0) * float(n_hilos)
    return 100.0 * (float(i) * r_total) / float(v)


# Obtiene la resistencia (ohm/km) del calibre desde una tabla base.
def r_de_tabla(tab: List[Dict[str, float]], awg: str) -> float:
    for t in tab:
        if str(t["awg"]) == str(awg):
            return float(t["r_ohm_km"])
    return float(tab[-1]["r_ohm_km"])


# Incrementa calibre dentro de la tabla hasta cumplir la VD objetivo.
def mejorar_por_vd(
    tab: List[Dict[str, float]],
    *,
    awg: str,
    i_a: float,
    v_v: float,
    l_m: float,
    vd_obj_pct: float,
    n_hilos: int = 2,
) -> str:
    idx = next((i for i, t in enumerate(tab) if str(t["awg"]) == str(awg)), 0)

    while idx < len(tab) - 1:
        vd = caida_tension_pct(
            v=v_v,
            i=i_a,
            l_m=l_m,
            r_ohm_km=float(tab[idx]["r_ohm_km"]),
            n_hilos=n_hilos,
        )
        if vd <= float(vd_obj_pct):
            break
        idx += 1

    return str(tab[idx]["awg"])
