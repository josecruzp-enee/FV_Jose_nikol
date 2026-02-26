# electrical/calculo_conductores.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from electrical.conductores.cables_conductores import tabla_base_conductores
from electrical.conductores.factores_nec import ampacidad_ajustada_nec
from electrical.conductores.modelo_tramo import (
    caida_tension_pct,
    mejorar_por_vd as _mejorar_por_vd_base,
)


def tabla_conductores(material: str = "Cu") -> List[Dict[str, Any]]:
    """
    Fuente única de tabla base (ampacidad + resistencia) Cu/Al.
    Formato estándar: {"awg": "10", "amp_a": 35, "r_ohm_km": 3.277}
    """
    return tabla_base_conductores(material)


def vdrop_pct(i_a: float, r_ohm_km: float, l_m: float, v_base: float, *, n_hilos: int = 2) -> float:
    return caida_tension_pct(v=float(v_base), i=float(i_a), l_m=float(l_m), r_ohm_km=float(r_ohm_km), n_hilos=int(n_hilos))


def seleccionar_por_ampacidad_nec(
    i_a: float,
    tabla: List[Dict[str, Any]],
    *,
    t_amb_c: float,
    ccc: int,
    aplicar_derating: bool,
) -> Dict[str, Any]:
    """
    Selecciona el primer conductor cuya ampacidad ajustada NEC >= i_a.
    """
    x = float(i_a)
    ccc = max(1, int(ccc))

    for t in tabla:
        amp_adj, _, _ = ampacidad_ajustada_nec(float(t["amp_a"]), float(t_amb_c), ccc, aplicar=bool(aplicar_derating))
        if x <= amp_adj:
            return dict(t)

    return dict(tabla[-1])


def mejorar_por_vd(
    cand: Dict[str, Any],
    *,
    i_a: float,
    v_base: float,
    l_m: float,
    vd_obj_pct: float,
    tabla: List[Dict[str, Any]],
    n_hilos: int,
) -> Dict[str, Any]:
    """
    Si la caída de tensión excede el objetivo, sube calibre usando mejorar_por_vd_base.
    """
    awg = _mejorar_por_vd_base(
        tabla,
        awg=str(cand["awg"]),
        i_a=float(i_a),
        v_v=float(v_base),
        l_m=float(l_m),
        vd_obj_pct=float(vd_obj_pct),
        n_hilos=int(n_hilos),
    )
    return next((dict(t) for t in tabla if str(t.get("awg")) == str(awg)), dict(tabla[-1]))


def tramo_conductor(
    *,
    nombre: str,
    i_a: float,
    v_base: float,
    l_m: float,
    vd_obj_pct: float,
    material: str = "Cu",
    n_hilos: int = 2,
    nec: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Motor único: selecciona calibre por ampacidad ajustada NEC + mejora por VD.
    """
    if i_a <= 0 or l_m <= 0 or v_base <= 0:
        return {"nombre": nombre, "ok": False, "nota": "Datos insuficientes para conductor/VD."}

    nec = nec or {}
    t_amb_c = float(nec.get("t_amb_c", 30.0))
    aplicar = bool(nec.get("aplicar_derating", True))
    ccc = int(nec.get("ccc", n_hilos))

    tab = tabla_conductores(material)
    cand = seleccionar_por_ampacidad_nec(i_a, tab, t_amb_c=t_amb_c, ccc=ccc, aplicar_derating=aplicar)
    best = mejorar_por_vd(cand, i_a=float(i_a), v_base=float(v_base), l_m=float(l_m),
                          vd_obj_pct=float(vd_obj_pct), tabla=tab, n_hilos=int(n_hilos))

    amp_adj, f_t, f_c = ampacidad_ajustada_nec(float(best["amp_a"]), t_amb_c, ccc, aplicar=aplicar)
    vd = vdrop_pct(float(i_a), float(best["r_ohm_km"]), float(l_m), float(v_base), n_hilos=int(n_hilos))

    return {
        "nombre": nombre,
        "ok": True,
        "i_a": round(float(i_a), 2),
        "l_m": round(float(l_m), 2),
        "v_base_v": round(float(v_base), 2),
        "awg": str(best["awg"]),
        "amp_base_a": float(best["amp_a"]),
        "amp_ajustada_a": round(float(amp_adj), 2),
        "fac_temp": round(float(f_t), 3),
        "fac_ccc": round(float(f_c), 3),
        "vd_pct": round(float(vd), 3),
        "vd_obj_pct": float(vd_obj_pct),
        "n_hilos": int(n_hilos),
        "material": str(material),
        "nec": {"t_amb_c": t_amb_c, "ccc": ccc, "aplicar_derating": aplicar},
    }
