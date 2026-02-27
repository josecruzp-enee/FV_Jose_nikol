"""
Modelo físico del tramo — FV Engine.

Responsabilidad:
- Cálculo de caída de tensión (VD) con resistencia DC referencial.
- Utilidades físicas sobre tablas (sin NEC, sin selección por ampacidad).
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def caida_tension_pct(
    *,
    v: float,
    i: float,
    l_m: float,
    r_ohm_km: float,
    n_hilos: int = 2,
) -> float:
    """
    Caída de tensión porcentual usando modelo resistivo DC simplificado:

        VD% = 100 * (I * R_total) / V
        R_total = r_ohm_km * (L_km) * n_hilos

    Donde n_hilos representa el número de conductores en el camino de corriente
    (por ejemplo, 2 para ida-vuelta en DC o 1Φ con retorno).
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

    if v <= 0.0 or i <= 0.0 or l_m <= 0.0 or r_ohm_km <= 0.0:
        return 0.0

    r_total = r_ohm_km * (l_m / 1000.0) * float(n_hilos)
    return 100.0 * (i * r_total) / v


def r_de_tabla(tab: List[Dict[str, float]], awg: str) -> float:
    """
    Obtiene la resistencia (ohm/km) del calibre desde una tabla base.

    Si no encuentra el calibre:
      - retorna 0.0 (para que el motor detecte inconsistencia / no se "auto-corrija").
    """
    a = str(awg)
    for t in tab:
        if str(t.get("awg")) == a:
            return float(t.get("r_ohm_km", 0.0))
    return 0.0


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
    Incrementa calibre dentro de la tabla hasta cumplir la VD objetivo.
    Devuelve el AWG final (puede terminar en el máximo si no logra cumplir).
    """
    a0 = str(awg)
    try:
        i_a = float(i_a)
        v_v = float(v_v)
        l_m = float(l_m)
        vd_obj_pct = float(vd_obj_pct)
        n_hilos = int(n_hilos)
    except Exception:
        return a0

    # Localiza índice inicial; si no existe, arranca en el primer calibre.
    idx0 = next((k for k, t in enumerate(tab) if str(t.get("awg")) == a0), 0)

    idx = idx0
    while idx < len(tab):
        vd = caida_tension_pct(
            v=v_v,
            i=i_a,
            l_m=l_m,
            r_ohm_km=float(tab[idx].get("r_ohm_km", 0.0)),
            n_hilos=n_hilos,
        )
        if vd <= vd_obj_pct:
            return str(tab[idx].get("awg"))
        idx += 1

    # No cumplió ni con el máximo; devuelve el último calibre disponible.
    return str(tab[-1].get("awg"))
