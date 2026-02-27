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

from typing import Any, Dict, List, Optional, Tuple

from .cables_conductores import tabla_base_conductores
from .factores_nec import ampacidad_ajustada_nec
from .modelo_tramo import caida_tension_pct, mejorar_por_vd, r_de_tabla

# Referencias normativas utilizadas en este módulo
NEC_REFERENCIAS = [
    "NEC 310.15(B)(1) - Ambient Temperature Correction",
    "NEC 310.15(C)(1) - Adjustment Factors for CCC",
    "NEC 215.2(A)(1) Informational Note - Voltage Drop Guidance",
    "NEC 210.19(A)(1) Informational Note - Voltage Drop Guidance",
    # "NEC 310.16 - Ampacity Tables (pendiente: migrar tablas completas)",
]


# ==========================================================
# Utilidades internas
# ==========================================================

def tabla_conductores(material: str = "Cu") -> List[Dict[str, Any]]:
    """Retorna la tabla base de conductores según material (Cu/Al)."""
    return list(tabla_base_conductores(material))


def _fila_por_awg(tabla: List[Dict[str, Any]], awg: str) -> Optional[Dict[str, Any]]:
    a = str(awg)
    for t in tabla:
        if str(t.get("awg")) == a:
            return dict(t)
    return None


def vdrop_pct(
    i_a: float,
    r_ohm_km: float,
    l_m: float,
    v_base: float,
    *,
    n_hilos: int = 2,
) -> float:
    """Wrapper VD% (delegación directa al modelo físico)."""
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
    Selecciona el primer conductor que soporta corriente por ampacidad ajustada
    NEC 310.15 (temperatura + CCC). Devuelve la fila base seleccionada.
    """
    if not tabla:
        return {}

    x = float(i_a)
    ccc = max(1, int(ccc))
    t_amb_c = float(t_amb_c)

    for t in tabla:
        amp_base = float(t.get("amp_a", 0.0))
        amp_adj, _, _ = ampacidad_ajustada_nec(
            amp_base,
            t_amb_c,
            ccc,
            aplicar=bool(aplicar_derating),
        )
        if x <= float(amp_adj):
            return dict(t)

    return dict(tabla[-1])


# ==========================================================
# Motor principal
# ==========================================================

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
    Dimensiona un tramo:
      1) Selecciona calibre por ampacidad ajustada NEC (310.15).
      2) Mejora por caída de tensión (informational notes) subiendo calibre.
      3) Entrega resultado estable para UI/PDF.

    Entradas:
      - i_diseno_a: corriente de diseño (ya incluye 125% u otro criterio).
      - v_base_v: tensión base del tramo (Vmp para DC, Vac/Vll para AC).
      - n_hilos: número de conductores en el camino de corriente del modelo VD
                 (DC: 2, AC 1Φ: 2, AC 3Φ (modelo simple): 3 si así lo manejas).
      - nec: {"t_amb_c": 30, "ccc": ..., "aplicar_derating": True}
    """
    # Validación mínima
    if float(i_diseno_a) <= 0 or float(l_m) <= 0 or float(v_base_v) <= 0:
        return {
            "nombre": str(nombre),
            "ok": False,
            "cumple": False,
            "nota": "Datos insuficientes para dimensionamiento de conductor.",
        }

    nec = nec or {}
    t_amb_c = float(nec.get("t_amb_c", 30.0))
    aplicar = bool(nec.get("aplicar_derating", True))

    # CCC: por defecto usa n_hilos, pero NEC CCC real puede ser distinto
    ccc = int(nec.get("ccc", n_hilos))
    ccc = max(1, ccc)

    tab = tabla_conductores(material)
    if not tab:
        return {
            "nombre": str(nombre),
            "ok": False,
            "cumple": False,
            "nota": f"Tabla de conductores vacía para material={material!r}.",
        }

    # 1) Selección por ampacidad NEC
    cand = seleccionar_por_ampacidad_nec(
        float(i_diseno_a),
        tab,
        t_amb_c=t_amb_c,
        ccc=ccc,
        aplicar_derating=aplicar,
    )
    awg_cand = str(cand.get("awg", tab[0].get("awg")))

    # 2) Mejora por VD (devuelve AWG final)
    awg_final = mejorar_por_vd(
        tab,
        awg=awg_cand,
        i_a=float(i_diseno_a),
        v_v=float(v_base_v),
        l_m=float(l_m),
        vd_obj_pct=float(vd_obj_pct),
        n_hilos=int(n_hilos),
    )

    fila_final = _fila_por_awg(tab, awg_final) or dict(tab[-1])
    awg_final = str(fila_final.get("awg"))

    # 3) Cálculos finales (ampacidad ajustada y VD)
    amp_base = float(fila_final.get("amp_a", 0.0))
    r_ohm_km = float(fila_final.get("r_ohm_km", 0.0))

    amp_adj, f_t, f_c = ampacidad_ajustada_nec(
        amp_base,
        t_amb_c,
        ccc,
        aplicar=aplicar,
    )

    vd_pct = caida_tension_pct(
        v=float(v_base_v),
        i=float(i_diseno_a),
        l_m=float(l_m),
        r_ohm_km=float(r_ohm_km),
        n_hilos=int(n_hilos),
    )

    cumple_amp = float(amp_adj) >= float(i_diseno_a)
    cumple_vd = float(vd_pct) <= float(vd_obj_pct)
    cumple = bool(cumple_amp and cumple_vd)

    # Detectar si se agotó tabla por VD (útil para notas)
    agotado_vd = (awg_final == str(tab[-1].get("awg"))) and (float(vd_pct) > float(vd_obj_pct))

    out: Dict[str, Any] = {
        "nombre": str(nombre),
        "ok": True,

        "i_diseno_a": round(float(i_diseno_a), 3),
        "l_m": round(float(l_m), 3),
        "v_base_v": round(float(v_base_v), 3),
        "material": str(material),
        "n_hilos": int(n_hilos),

        "calibre": awg_final,
        "awg": awg_final,  # compat legacy

        "ampacidad_base_a": round(float(amp_base), 3),
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
        "agotado_vd": bool(agotado_vd),
        "referencias": list(NEC_REFERENCIAS),
    }

    if not cumple:
        notas: List[str] = []
        if not cumple_amp:
            notas.append("No cumple ampacidad ajustada NEC (310.15).")
        if not cumple_vd:
            if agotado_vd:
                notas.append("No cumple caída de tensión objetivo ni con el calibre máximo de la tabla.")
            else:
                notas.append("No cumple caída de tensión objetivo; se requiere aumentar calibre.")
        out["nota"] = " ".join(notas)

    return out


# ==========================================================
# Wrappers legacy (presets) — delegan al motor único
# ==========================================================

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
    res.setdefault("i_diseno_a", round(float(i_diseno), 3))
    return res


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

    # Ojo: este modelo VD es resistivo “lineal” (no usa √3).
    # Si luego implementas VD 3Φ con √3, hazlo en modelo_tramo (fuente única).
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
    "tramo_conductor",
    "tramo_dc_ref",
    "tramo_ac_1f_ref",
    "tramo_ac_3f_ref",
]
