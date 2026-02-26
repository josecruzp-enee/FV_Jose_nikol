# electrical/conductores/modelo_tramo.py
from __future__ import annotations

from typing import Dict, List


# ==========================================================
# MODELO FÍSICO DEL TRAMO
# (NO NEC — NO selección de calibre)
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
    Calcula caída de tensión porcentual.

    ΔV% = I · R_total / V · 100
    """

    if v <= 0 or i <= 0 or l_m <= 0 or r_ohm_km <= 0:
        return 0.0

    r_total = float(r_ohm_km) * (float(l_m) / 1000.0) * float(n_hilos)
    return 100.0 * (float(i) * r_total) / float(v)


# ==========================================================
# UTILIDADES SOBRE TABLAS
# ==========================================================

def r_de_tabla(tab: List[Dict[str, float]], awg: str) -> float:
    """
    Obtiene resistencia desde tabla base.
    """
    for t in tab:
        if str(t["awg"]) == str(awg):
            return float(t["r_ohm_km"])

    # fallback → calibre más grueso
    return float(tab[-1]["r_ohm_km"])


# ==========================================================
# MEJORA POR CAÍDA DE TENSIÓN
# ==========================================================

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
    """
    Incrementa calibre hasta cumplir VD objetivo.
    NO evalúa ampacidad (eso lo hace calculo_conductores).
    """

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
