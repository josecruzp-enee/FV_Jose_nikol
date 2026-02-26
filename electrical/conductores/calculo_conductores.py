"""
calculo_conductores.py — FV Engine

Motor de dimensionamiento de conductores.

Responsabilidad:
- Selección de calibre por ampacidad ajustada (derating).
- Verificación y mejora por caída de tensión.
- Entrega de resultado estable para UI/PDF/orquestador.

Notas normativas:
- Ampacidad base proviene de tablas (referencial; luego migrar a NEC 310.16 completo).
- Correcciones por temperatura y CCC: NEC 310.15(B)(1) y 310.15(C)(1).
- Caída de tensión: guía práctica basada en NEC 215.2 y 210.19 (Informational Notes).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from electrical.conductores.cables_conductores import tabla_base_conductores
from electrical.conductores.factores_nec import ampacidad_ajustada_nec
from electrical.conductores.modelo_tramo import (
    caida_tension_pct,
    mejorar_por_vd as _mejorar_por_vd_base,
)

# Referencias normativas utilizadas en este módulo
NEC_REFERENCIAS = [
    "NEC 310.15(B)(1) - Ambient Temperature Correction",
    "NEC 310.15(C)(1) - Adjustment Factors for CCC",
    "NEC 215.2(A)(1) Informational Note - Voltage Drop Guidance",
    "NEC 210.19(A)(1) Informational Note - Voltage Drop Guidance",
    # "NEC 310.16 - Ampacity Tables (pendiente: migrar tablas completas)",
]


# Retorna la tabla base de conductores según material (Cu/Al) como insumo de selección.
def tabla_conductores(material: str = "Cu") -> List[Dict[str, Any]]:
    return list(tabla_base_conductores(material))


# Calcula caída de tensión porcentual de un tramo usando el modelo físico (VD%).
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


# Selecciona el primer conductor que soporta corriente por ampacidad ajustada NEC 310.15 (temp y CCC).
def seleccionar_por_ampacidad_nec(
    i_a: float,
    tabla: List[Dict[str, Any]],
    *,
    t_amb_c: float,
    ccc: int,
    aplicar_derating: bool,
) -> Dict[str, Any]:
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


# Incrementa calibre hasta cumplir VD objetivo siguiendo guía de caída de tensión NEC (informational notes).
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
    if not tabla:
        return {}

    if not cand or "awg" not in cand:
        cand = dict(tabla[0])

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


# Dimensiona un tramo: selecciona calibre por ampacidad (NEC 310.15) y mejora por VD (NEC informational notes).
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

    cand = seleccionar_por_ampacidad_nec(
        float(i_diseno_a),
        tab,
        t_amb_c=t_amb_c,
        ccc=ccc,
        aplicar_derating=aplicar,
    )

    best = mejorar_por_vd(
        cand,
        i_a=float(i_diseno_a),
        v_base=float(v_base_v),
        l_m=float(l_m),
        vd_obj_pct=float(vd_obj_pct),
        tabla=tab,
        n_hilos=int(n_hilos),
    )

    amp_adj, f_t, f_c = ampacidad_ajustada_nec(float(best["amp_a"]), t_amb_c, ccc, aplicar=aplicar)
    r_ohm_km = float(best["r_ohm_km"])
    vd_pct = vdrop_pct(float(i_diseno_a), r_ohm_km, float(l_m), float(v_base_v), n_hilos=int(n_hilos))

    cumple_amp = float(amp_adj) >= float(i_diseno_a)
    cumple_vd = float(vd_pct) <= float(vd_obj_pct)
    cumple = bool(cumple_amp and cumple_vd)

    out = {
        "nombre": str(nombre),
        "ok": True,

        "i_diseno_a": round(float(i_diseno_a), 3),
        "l_m": round(float(l_m), 3),
        "v_base_v": round(float(v_base_v), 3),
        "material": str(material),
        "n_hilos": int(n_hilos),

        "calibre": str(best["awg"]),
        "awg": str(best["awg"]),  # compatibilidad legacy

        "ampacidad_base_a": float(best["amp_a"]),
        "ampacidad_ajustada_a": round(float(amp_adj), 3),

        "fac_temp": round(float(f_t), 4),
        "fac_ccc": round(float(f_c), 4),

        "r_ohm_km": round(float(r_ohm_km), 6),
        "vd_pct": round(float(vd_pct), 4),
        "vd_obj_pct": float(vd_obj_pct),

        "cumple_ampacidad": bool(cumple_amp),
        "cumple_vd": bool(cumple_vd),
        "cumple": bool(cumple),

        "nec": {"t_amb_c": t_amb_c, "ccc": int(ccc), "aplicar_derating": bool(aplicar)},
    }

    if not cumple:
        notas = []
        if not cumple_amp:
            notas.append("No cumple ampacidad ajustada NEC.")
        if not cumple_vd:
            notas.append("No cumple caída de tensión objetivo.")
        out["nota"] = " ".join(notas)

    return out


# Wrapper DC legacy: calcula i_diseno y delega a tramo_conductor() (motor único).
def tramo_dc_ref(
    *,
    vmp_v: float,
    imp_a: float,
    isc_a: Optional[float],
    dist_m: float,
    factor_seguridad: float = 1.25,
    vd_obj_pct: float = 2.0,
    material: str = "Cu",
    nec: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    base_i = float(isc_a) if isc_a is not None else float(imp_a)
    i_diseno = float(base_i) * float(factor_seguridad)

    res = tramo_conductor(
        nombre="TRAMO_DC",
        i_diseno_a=float(i_diseno),
        v_base_v=float(vmp_v),
        l_m=float(dist_m),
        vd_obj_pct=float(vd_obj_pct),
        material=str(material),
        n_hilos=2,
        nec=nec,
    )

    # Compat: conserva campos mínimos históricos
    res.setdefault("i_diseno_a", round(float(i_diseno), 3))
    return res


# Wrapper AC 1F legacy: calcula i_diseno y delega a tramo_conductor() (motor único).
def tramo_ac_1f_ref(
    *,
    vac_v: float,
    iac_a: float,
    dist_m: float,
    factor_seguridad: float = 1.25,
    vd_obj_pct: float = 2.0,
    material: str = "Cu",
    nec: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    i_diseno = float(iac_a) * float(factor_seguridad)

    res = tramo_conductor(
        nombre="TRAMO_AC_1F",
        i_diseno_a=float(i_diseno),
        v_base_v=float(vac_v),
        l_m=float(dist_m),
        vd_obj_pct=float(vd_obj_pct),
        material=str(material),
        n_hilos=2,
        nec=nec,
    )

    res.setdefault("i_diseno_a", round(float(i_diseno), 3))
    return res


# Wrapper AC 3F legacy: calcula i_diseno y delega a tramo_conductor() (motor único).
def tramo_ac_3f_ref(
    *,
    vll_v: float,
    iac_a: float,
    dist_m: float,
    factor_seguridad: float = 1.25,
    vd_obj_pct: float = 2.0,
    material: str = "Cu",
    nec: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    i_diseno = float(iac_a) * float(factor_seguridad)

    res = tramo_conductor(
        nombre="TRAMO_AC_3F",
        i_diseno_a=float(i_diseno),
        v_base_v=float(vll_v),
        l_m=float(dist_m),
        vd_obj_pct=float(vd_obj_pct),
        material=str(material),
        n_hilos=3,
        nec=nec,
    )

    res.setdefault("i_diseno_a", round(float(i_diseno), 3))
    return res


__all__ = [
    "NEC_REFERENCIAS",
    "tabla_conductores",
    "vdrop_pct",
    "seleccionar_por_ampacidad_nec",
    "mejorar_por_vd",
    "tramo_conductor",
    "tramo_dc_ref",
    "tramo_ac_1f_ref",
    "tramo_ac_3f_ref",
]
