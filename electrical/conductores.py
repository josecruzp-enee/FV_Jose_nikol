# electrical/conductores.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, List

from electrical.modelos import SeleccionConductor


# Tabla mínima (referencial) Cu THHN/THWN-2 a 75°C (NEC 310.16 aprox; ajustar luego)
# OJO: para comercial real: esto debe venir de catálogo + correcciones.
AMPACIDAD_CU_75C: Dict[str, float] = {
    "14 AWG": 20,
    "12 AWG": 25,
    "10 AWG": 35,
    "8 AWG": 50,
    "6 AWG": 65,
    "4 AWG": 85,
    "3 AWG": 100,
    "2 AWG": 115,
    "1 AWG": 130,
    "1/0 AWG": 150,
    "2/0 AWG": 175,
    "3/0 AWG": 200,
    "4/0 AWG": 230,
}

# Resistencias aproximadas Cu a 20°C en ohm/km (para caída simple). Ajustar con temp luego.
R_OHM_KM_CU: Dict[str, float] = {
    "14 AWG": 8.286,
    "12 AWG": 5.211,
    "10 AWG": 3.277,
    "8 AWG": 2.061,
    "6 AWG": 1.296,
    "4 AWG": 0.815,
    "3 AWG": 0.646,
    "2 AWG": 0.513,
    "1 AWG": 0.407,
    "1/0 AWG": 0.323,
    "2/0 AWG": 0.256,
    "3/0 AWG": 0.203,
    "4/0 AWG": 0.161,
}


def _seleccionar_por_ampacidad(i_diseno: float, tabla_amp: Dict[str, float]) -> str:
    for calibre, amp in tabla_amp.items():
        if amp >= i_diseno:
            return calibre
    # si no alcanza, devuelve el mayor
    return list(tabla_amp.keys())[-1]


def _caida_tension_dc_pct(i_a: float, v_v: float, dist_m: float, calibre: str) -> float:
    """
    Caída DC simple: Vdrop = I * R_total
    R_total = 2 * R(ohm/m) * L
    """
    if v_v <= 0:
        return 0.0
    r_ohm_km = R_OHM_KM_CU.get(calibre)
    if r_ohm_km is None:
        return 0.0
    r_ohm_m = r_ohm_km / 1000.0
    r_total = 2.0 * r_ohm_m * dist_m
    vdrop = i_a * r_total
    return (vdrop / v_v) * 100.0


def _caida_tension_ac_pct(i_a: float, v_v: float, dist_m: float, calibre: str, fases: int) -> float:
    """
    Caída AC simplificada (solo R): monofásico ≈ 2*L, trifásico ≈ sqrt(3)*L.
    """
    if v_v <= 0:
        return 0.0
    r_ohm_km = R_OHM_KM_CU.get(calibre)
    if r_ohm_km is None:
        return 0.0
    r_ohm_m = r_ohm_km / 1000.0

    if fases == 3:
        import math
        vdrop = math.sqrt(3) * i_a * r_ohm_m * dist_m
    else:
        vdrop = 2.0 * i_a * r_ohm_m * dist_m

    return (vdrop / v_v) * 100.0


def seleccionar_conductor_dc(i_dc_diseno_a: float, v_dc_v: float, dist_m: float, cfg: dict) -> SeleccionConductor:
    objetivo = float(cfg.get("caida_tension_objetivo_pct", 2.0))

    calibre = _seleccionar_por_ampacidad(i_dc_diseno_a, AMPACIDAD_CU_75C)
    caida = _caida_tension_dc_pct(i_dc_diseno_a, v_dc_v, dist_m, calibre)

    obs: List[str] = []
    if caida > objetivo:
        obs.append(f"Caída DC {caida:.2f}% > objetivo {objetivo:.2f}% (subir calibre o reducir distancia).")

    return SeleccionConductor(
        calibre=calibre,
        material="Cu",
        ampacidad_a=float(AMPACIDAD_CU_75C[calibre]),
        caida_tension_pct=float(caida),
        observaciones=obs,
    )


def seleccionar_conductor_ac(i_ac_diseno_a: float, v_ac_v: float, dist_m: float, fases: int, cfg: dict) -> SeleccionConductor:
    objetivo = float(cfg.get("caida_tension_objetivo_pct", 2.0))

    calibre = _seleccionar_por_ampacidad(i_ac_diseno_a, AMPACIDAD_CU_75C)
    caida = _caida_tension_ac_pct(i_ac_diseno_a, v_ac_v, dist_m, calibre, fases=fases)

    obs: List[str] = []
    if caida > objetivo:
        obs.append(f"Caída AC {caida:.2f}% > objetivo {objetivo:.2f}% (subir calibre o reducir distancia).")

    return SeleccionConductor(
        calibre=calibre,
        material="Cu",
        ampacidad_a=float(AMPACIDAD_CU_75C[calibre]),
        caida_tension_pct=float(caida),
        observaciones=obs,
    )
