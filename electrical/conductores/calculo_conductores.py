# electrical/conductores/calculo_conductores.py
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

    Formato estándar por fila:
      {"awg": "10", "amp_a": 35, "r_ohm_km": 3.277}
    """
    return list(tabla_base_conductores(material))


def vdrop_pct(
    i_a: float,
    r_ohm_km: float,
    l_m: float,
    v_base: float,
    *,
    n_hilos: int = 2,
) -> float:
    return caida_tension_pct(
        v=float(v_base),
        i=float(i_a),
        l_m=float(l_m),
        r_ohm_km=float(r_ohm_km),
        n_hilos=int(n_hilos),
    )


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
    if not tabla:
        return {}

    x = float(i_a)
    ccc = max(1, int(ccc))

    for t in tabla:
        amp_adj, _, _ = ampacidad_ajustada_nec(
            float(t["amp_a"]),
            float(t_amb_c),
            ccc,
            aplicar=bool(aplicar_derating),
        )
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
    Si la caída de tensión excede el objetivo, sube calibre usando _mejorar_por_vd_base.
    """
    if not tabla:
        return {}

    if not cand or "awg" not in cand:
        cand = dict(tabla[0])

    awg = _mejorar_por_vd_base(
        tabla,  # tabla base con r_ohm_km
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
    i_diseno_a: float,
    v_base_v: float,
    l_m: float,
    vd_obj_pct: float,
    material: str = "Cu",
    n_hilos: int = 2,
    nec: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Motor único: selecciona calibre por:
      1) ampacidad ajustada NEC (derating por temp y CCC)
      2) mejora por caída de tensión (VD)

    Salida normalizada para UI/PDF + trazabilidad.
    """
    if i_diseno_a <= 0 or l_m <= 0 or v_base_v <= 0:
        return {
            "nombre": nombre,
            "ok": False,
            "cumple": False,
            "nota": "Datos insuficientes para conductor/VD.",
        }

    nec = nec or {}
    t_amb_c = float(nec.get("t_amb_c", 30.0))
    aplicar = bool(nec.get("aplicar_derating", True))
    ccc = int(nec.get("ccc", n_hilos))

    tab = tabla_conductores(material)
    if not tab:
        return {
            "nombre": nombre,
            "ok": False,
            "cumple": False,
            "nota": f"Tabla de conductores vacía para material={material!r}.",
        }

    # 1) por ampacidad NEC
    cand = seleccionar_por_ampacidad_nec(
        float(i_diseno_a),
        tab,
        t_amb_c=t_amb_c,
        ccc=ccc,
        aplicar_derating=aplicar,
    )

    # 2) mejora por VD
    best = mejorar_por_vd(
        cand,
        i_a=float(i_diseno_a),
        v_base=float(v_base_v),
        l_m=float(l_m),
        vd_obj_pct=float(vd_obj_pct),
        tabla=tab,
        n_hilos=int(n_hilos),
    )

    # cálculos finales del candidato seleccionado
    amp_adj, f_t, f_c = ampacidad_ajustada_nec(float(best["amp_a"]), t_amb_c, ccc, aplicar=aplicar)
    r_ohm_km = float(best["r_ohm_km"])
    vd_pct = vdrop_pct(float(i_diseno_a), r_ohm_km, float(l_m), float(v_base_v), n_hilos=int(n_hilos))

    cumple_amp = float(amp_adj) >= float(i_diseno_a)
    cumple_vd = float(vd_pct) <= float(vd_obj_pct)
    cumple = bool(cumple_amp and cumple_vd)

    # salida estable (y compatible con legacy)
    out = {
        "nombre": str(nombre),
        "ok": True,

        # contrato estable
        "i_diseno_a": round(float(i_diseno_a), 3),
        "l_m": round(float(l_m), 3),
        "v_base_v": round(float(v_base_v), 3),
        "material": str(material),
        "n_hilos": int(n_hilos),

        "calibre": str(best["awg"]),   # preferido
        "awg": str(best["awg"]),       # compat legacy

        "ampacidad_base_a": float(best["amp_a"]),
        "ampacidad_ajustada_a": round(float(amp_adj), 3),

        "fac_temp": round(float(f_t), 4),
        "fac_ccc": round(float(f_c), 4),

        "r_ohm_km": round(float(r_ohm_km), 6),
        "vd_pct": round(float(vd_pct), 4),
        "vd_obj_pct": float(vd_obj_pct),

        # checks
        "cumple_ampacidad": bool(cumple_amp),
        "cumple_vd": bool(cumple_vd),
        "cumple": bool(cumple),

        # trazabilidad NEC
        "nec": {"t_amb_c": t_amb_c, "ccc": int(ccc), "aplicar_derating": bool(aplicar)},
    }

    # si no cumple, no lo escondas: deja nota útil
    if not cumple:
        notas = []
        if not cumple_amp:
            notas.append("No cumple ampacidad ajustada NEC.")
        if not cumple_vd:
            notas.append("No cumple caída de tensión objetivo.")
        out["nota"] = " ".join(notas)

    return out
