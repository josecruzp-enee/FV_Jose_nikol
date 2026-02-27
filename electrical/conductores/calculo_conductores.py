"""
calculo_conductores.py — FV Engine

Motor de dimensionamiento de conductores.

Responsabilidad:
- Selección de calibre por ampacidad ajustada (derating).
- Verificación y mejora por caída de tensión.
- Entrega de resultado estable para UI/PDF/orquestador.

Extras (FV):
- Orquestador de tramos FV típicos (DC/AC) a partir de strings + inversor.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from .cables_conductores import tabla_base_conductores
from .factores_nec import ampacidad_ajustada_nec
from .modelo_tramo import caida_tension_pct, mejorar_por_vd
from .corrientes import calcular_corrientes

# Referencias normativas utilizadas en este módulo
NEC_REFERENCIAS = [
    "NEC 310.15(B)(1) - Ambient Temperature Correction",
    "NEC 310.15(C)(1) - Adjustment Factors for CCC",
    "NEC 215.2(A)(1) Informational Note - Voltage Drop Guidance",
    "NEC 210.19(A)(1) Informational Note - Voltage Drop Guidance",
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
# Motor principal (genérico)
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

    Convención VD:
      - Modelo resistivo simplificado (DC) del tramo.
      - n_hilos representa la cantidad de conductores en el camino resistivo.
      - Si luego implementas VD 3Φ con √3, hacerlo en modelo_tramo (fuente única).
    """
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

    ccc_provisto = "ccc" in nec
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

    # 2) Mejora por VD
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

    # 3) Cálculos finales
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
        "awg": awg_final,

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

    if not ccc_provisto:
        out["nota_ccc"] = "CCC no provisto; se usó n_hilos como aproximación."

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
# Orquestador FV: panel/string → inversor → tablero principal
# ==========================================================

def _f(m: Mapping[str, Any], k: str, default: float = 0.0) -> float:
    try:
        v = m.get(k, default)
        return float(v) if v is not None else float(default)
    except Exception:
        return float(default)


def dimensionar_tramos_fv(
    *,
    strings: Mapping[str, Any],
    inversor: Mapping[str, Any],
    params_cableado: Mapping[str, Any],
    cfg_tecnicos: Mapping[str, Any],
    material_dc: str = "Cu",
    material_ac: str = "Cu",
    nec_dc: Optional[Dict[str, Any]] = None,
    nec_ac: Optional[Dict[str, Any]] = None,
    distancias_m: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Construye tramos FV típicos y los dimensiona con el motor.

    Tramos que modela (por defecto):
      - DC_STRING_A_INV: string/array DC → inversor (usa dist_dc_m)
      - AC_INV_A_TABLERO: inversor → tablero principal (usa dist_ac_m)

    Si quieres separar "panel→string" y "string→inversor", pasa distancias_m:
      distancias_m = {
        "dc_panel_a_string": 5.0,
        "dc_string_a_inversor": 18.0,
        "ac_inversor_a_tabl_principal": 25.0,
      }

    params_cableado esperado (keys típicas):
      - dist_dc_m, dist_ac_m
      - vdrop_obj_dc_pct, vdrop_obj_ac_pct
      - vac (opcional)

    strings esperado (keys típicas):
      - vmp_string_v (o vmp_array_v / vmp_string_v)
      - (corrientes salen de calcular_corrientes)

    inversor esperado (keys típicas):
      - v_ac_nom_v / vac, fases
      - i_ac_max_a (opcional) o kw_ac/potencia_ac_kw
    """
    distancias_m = distancias_m or {}

    # 1) Corrientes de diseño (DC/AC)
    corr = calcular_corrientes(strings, inversor, cfg_tecnicos)

    # 2) Voltajes base
    vmp_dc = _f(strings, "vmp_string_v", 0.0)
    if vmp_dc <= 0.0:
        vmp_dc = _f(strings, "vmp_array_v", 0.0)

    vac = _f(params_cableado, "vac", 0.0)
    if vac <= 0.0:
        vac = _f(inversor, "v_ac_nom_v", 0.0)
    if vac <= 0.0:
        vac = _f(inversor, "vac", 0.0)

    # 3) Distancias / objetivos VD
    dist_dc = float(distancias_m.get("dc_string_a_inversor", _f(params_cableado, "dist_dc_m", 0.0)))
    dist_ac = float(distancias_m.get("ac_inversor_a_tabl_principal", _f(params_cableado, "dist_ac_m", 0.0)))

    vd_obj_dc = _f(params_cableado, "vdrop_obj_dc_pct", 2.0)
    vd_obj_ac = _f(params_cableado, "vdrop_obj_ac_pct", 2.0)

    # 4) Dimensionamiento tramos
    out_tramos: Dict[str, Any] = {}

    # (Opcional) panel → string (si te pasan distancia)
    dist_panel_string = distancias_m.get("dc_panel_a_string", 0.0)
    if dist_panel_string and dist_panel_string > 0.0 and vmp_dc > 0.0:
        out_tramos["DC_PANEL_A_STRING"] = tramo_conductor(
            nombre="DC_PANEL_A_STRING",
            i_diseno_a=float(corr.get("i_dc_diseno_a", 0.0)),
            v_base_v=float(vmp_dc),
            l_m=float(dist_panel_string),
            vd_obj_pct=float(vd_obj_dc),
            material=str(material_dc),
            n_hilos=2,
            nec=nec_dc,
        )

    # string/array → inversor (principal DC)
    out_tramos["DC_STRING_A_INV"] = tramo_conductor(
        nombre="DC_STRING_A_INV",
        i_diseno_a=float(corr.get("i_dc_diseno_a", 0.0)),
        v_base_v=float(vmp_dc) if vmp_dc > 0.0 else 1.0,
        l_m=float(dist_dc),
        vd_obj_pct=float(vd_obj_dc),
        material=str(material_dc),
        n_hilos=2,
        nec=nec_dc,
    )

    # inversor → tablero principal (AC principal)
    # Nota: el VD aquí sigue el modelo resistivo simplificado del dominio.
    fases = int(inversor.get("fases", 1) or 1)
    n_hilos_ac = 3 if fases == 3 else 2

    out_tramos["AC_INV_A_TABLERO"] = tramo_conductor(
        nombre="AC_INV_A_TABLERO",
        i_diseno_a=float(corr.get("i_ac_diseno_a", 0.0)),
        v_base_v=float(vac) if vac > 0.0 else 1.0,
        l_m=float(dist_ac),
        vd_obj_pct=float(vd_obj_ac),
        material=str(material_ac),
        n_hilos=int(n_hilos_ac),
        nec=nec_ac,
    )

    return {
        "corrientes": dict(corr),
        "tramos": out_tramos,
        "meta": {
            "material_dc": str(material_dc),
            "material_ac": str(material_ac),
            "vd_obj_dc_pct": float(vd_obj_dc),
            "vd_obj_ac_pct": float(vd_obj_ac),
            "dist_dc_m": float(dist_dc),
            "dist_ac_m": float(dist_ac),
        },
    }


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
    "dimensionar_tramos_fv",
    "tramo_dc_ref",
    "tramo_ac_1f_ref",
    "tramo_ac_3f_ref",
]
