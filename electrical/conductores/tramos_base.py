from __future__ import annotations

from typing import Dict, List

from electrical.conductores.cables_conductores import ampacidad, calibres, idx_calibre, resistencia_cu_ohm_km, tabla_base


def caida_tension_pct(*, v: float, i: float, l_m: float, r_ohm_km: float, n_hilos: int) -> float:
    if v <= 0 or i <= 0 or l_m <= 0 or r_ohm_km <= 0:
        return 0.0
    r_total = float(r_ohm_km) * (float(l_m) / 1000.0) * float(n_hilos)
    return 100.0 * (float(i) * r_total) / float(v)


def r_cu_ohm_km(awg: str) -> float:
    return resistencia_cu_ohm_km(str(awg))


def max_calibre(c1: str, c2: str, *, tipo: str) -> str:
    return c1 if idx_calibre(c1, tipo=tipo) > idx_calibre(c2, tipo=tipo) else c2


def elegir_por_ampacidad(*, i_diseno_a: float, tipo: str) -> str:
    for g in calibres(tipo):
        if ampacidad(g, tipo=tipo) >= float(i_diseno_a):
            return g
    return calibres(tipo)[-1]


def elegir_por_regulacion(*, v: float, i: float, l_m: float, vd_obj_pct: float, tipo: str, n_hilos: int) -> str:
    for g in calibres(tipo):
        vd = caida_tension_pct(v=v, i=i, l_m=l_m, r_ohm_km=r_cu_ohm_km(g), n_hilos=n_hilos)
        if vd <= float(vd_obj_pct):
            return g
    return calibres(tipo)[-1]


def elegir_calibre(*, v: float, i: float, i_diseno_a: float, l_m: float, vd_obj_pct: float, tipo: str, n_hilos: int) -> str:
    g_amp = elegir_por_ampacidad(i_diseno_a=i_diseno_a, tipo=tipo)
    g_vd = elegir_por_regulacion(v=v, i=i, l_m=l_m, vd_obj_pct=vd_obj_pct, tipo=tipo, n_hilos=n_hilos)
    return max_calibre(g_amp, g_vd, tipo=tipo)


def r_de_tabla(tab: List[Dict[str, float]], awg: str) -> float:
    for t in tab:
        if str(t["awg"]) == str(awg):
            return float(t["r_ohm_km"])
    return float(tab[-1]["r_ohm_km"])


def primero_por_amp(tab: List[Dict[str, float]], *, i_a: float) -> str:
    for t in tab:
        if float(i_a) <= float(t["amp_a"]):
            return str(t["awg"])
    return str(tab[-1]["awg"])


def mejorar_por_vd(tab: List[Dict[str, float]], *, awg: str, i_a: float, v_v: float, l_m: float, vd_obj_pct: float, n_hilos: int) -> str:
    idx = next((i for i, t in enumerate(tab) if str(t["awg"]) == str(awg)), 0)
    while idx < len(tab) - 1:
        vd = caida_tension_pct(v=v_v, i=i_a, l_m=l_m, r_ohm_km=float(tab[idx]["r_ohm_km"]), n_hilos=n_hilos)
        if vd <= float(vd_obj_pct):
            break
        idx += 1
    return str(tab[idx]["awg"])


def elegir_por_tabla(tab: List[Dict[str, float]], *, i_a: float, v_v: float, l_m: float, vd_obj_pct: float, n_hilos: int) -> str:
    cand = primero_por_amp(tab, i_a=i_a)
    return mejorar_por_vd(tab, awg=cand, i_a=i_a, v_v=v_v, l_m=l_m, vd_obj_pct=vd_obj_pct, n_hilos=n_hilos)


def tramo_tabla_base(*, nombre: str, material: str, i_a: float, v_v: float, l_m: float, vd_obj_pct: float, n_hilos: int) -> Dict[str, float | str | bool]:
    tab = tabla_base(material)
    if i_a <= 0 or v_v <= 0 or l_m <= 0:
        return {"nombre": nombre, "ok": False, "nota": "Datos insuficientes."}
    awg = elegir_por_tabla(tab, i_a=i_a, v_v=v_v, l_m=l_m, vd_obj_pct=vd_obj_pct, n_hilos=n_hilos)
    r = r_de_tabla(tab, awg)
    vd = caida_tension_pct(v=v_v, i=i_a, l_m=l_m, r_ohm_km=r, n_hilos=n_hilos)
    return {"nombre": nombre, "ok": True, "awg": awg, "vd_pct": round(vd, 3), "vd_obj_pct": float(vd_obj_pct), "material": material}
