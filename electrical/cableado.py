# electrical/cableado.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import math

from electrical.modelos import ParametrosCableado


# ==========================================================
# Tablas (referenciales)
# ==========================================================

# Ampacidad CU 75°C (simplificada)
AMP_CU_75C = {"14": 20, "12": 25, "10": 35, "8": 50, "6": 65, "4": 85, "3": 100, "2": 115, "1": 130, "1/0": 150}

# PV wire referencial
AMP_PV_90C = {"14": 25, "12": 30, "10": 40, "8": 55, "6": 75}

# R ohm/km Cu
R_OHM_KM_CU = {"14": 8.286, "12": 5.211, "10": 3.277, "8": 2.061, "6": 1.296, "4": 0.815, "3": 0.647, "2": 0.513, "1": 0.407, "1/0": 0.323}

GAUGES_CU = ["14", "12", "10", "8", "6", "4", "3", "2", "1", "1/0"]
GAUGES_PV = ["14", "12", "10", "8", "6"]


# ==========================================================
# Utils pequeños
# ==========================================================

def _cfg_get(cfg_tecnicos: Optional[Dict[str, Any]], key: str, default: float) -> float:
    if not cfg_tecnicos:
        return float(default)
    try:
        return float(cfg_tecnicos.get(key, default))
    except Exception:
        return float(default)


def _vdrop_pct_2wire(V: float, I: float, L_m: float, gauge: str) -> float:
    R_m = (R_OHM_KM_CU[gauge] / 1000.0)
    vdrop = 2.0 * I * R_m * L_m
    return (vdrop / V) * 100.0


def _pick_by_ampacity(table: dict, I: float, gauges: List[str]) -> str:
    for g in gauges:
        if table.get(g, 0) >= I:
            return g
    return gauges[-1]


def _pick_by_vdrop(V: float, I: float, L_m: float, target_pct: float, gauges: List[str]) -> str:
    for g in gauges:
        if _vdrop_pct_2wire(V, I, L_m, g) <= target_pct:
            return g
    return gauges[-1]


def _max_gauge(g1: str, g2: str, gauges: List[str]) -> str:
    # el "mayor" es el de índice más alto en la lista (más grueso)
    return g1 if gauges.index(g1) > gauges.index(g2) else g2


def _breaker_sugerido(i_continua: float) -> int:
    for b in [30, 40, 50, 60, 70, 80, 90, 100]:
        if i_continua <= b:
            return b
    return 125


def _conduit_heuristico(ac_gauge: str, incluye_neutro: bool, extra_ccc: int) -> str:
    ccc = 2 + (1 if incluye_neutro else 0) + max(0, int(extra_ccc))

    if ac_gauge in ["14", "12", "10", "8"]:
        base = '1/2"'
    elif ac_gauge == "6":
        base = '3/4"'
    else:
        base = '1"'

    if ccc >= 4:
        if base == '1/2"':
            return '3/4"'
        if base == '3/4"':
            return '1"'
        return '1-1/4"'

    return base


# ==========================================================
# Subcálculos (funciones cortas)
# ==========================================================

def _calcular_ac(
    *,
    params: ParametrosCableado,
    iac_estimado_a: float,
    cfg_tecnicos: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Selección AC:
      - I diseño = iac_estimado * factor_seguridad_ac (default 1.25)
      - gauge por ampacidad y por vdrop (elige el mayor)
      - retorna gauge, vdrop, breaker, conduit, tierra
    """
    f_ac = _cfg_get(cfg_tecnicos, "factor_seguridad_ac", 1.25)
    vdrop_obj_ac = _cfg_get(cfg_tecnicos, "vdrop_obj_ac_pct", float(getattr(params, "vdrop_obj_ac_pct", 2.0)))

    i_ac_diseno = float(iac_estimado_a) * float(f_ac)

    g_amp = _pick_by_ampacity(AMP_CU_75C, i_ac_diseno, GAUGES_CU)
    g_vd = _pick_by_vdrop(float(params.vac), float(iac_estimado_a), float(params.dist_ac_m), float(vdrop_obj_ac), GAUGES_CU)
    g_ac = _max_gauge(g_amp, g_vd, GAUGES_CU)

    vd_ac = _vdrop_pct_2wire(float(params.vac), float(iac_estimado_a), float(params.dist_ac_m), g_ac)

    breaker = _breaker_sugerido(i_ac_diseno)
    conduit = _conduit_heuristico(g_ac, bool(params.incluye_neutro_ac), int(params.otros_ccc))
    tierra = "10" if GAUGES_CU.index(g_ac) >= GAUGES_CU.index("6") else "12"

    return {
        "gauge_awg": g_ac,
        "vdrop_pct": round(vd_ac, 2),
        "breaker_a": int(breaker),
        "conduit": str(conduit),
        "tierra_awg": str(tierra),
        "vdrop_obj_pct": float(vdrop_obj_ac),
        "i_diseno_a": float(i_ac_diseno),
        "factor_seguridad": float(f_ac),
    }


def _calcular_dc(
    *,
    params: ParametrosCableado,
    vmp_string_v: float,
    imp_a: float,
    isc_a: Optional[float],
    cfg_tecnicos: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Selección DC:
      - I diseño = (Isc o Imp) * factor_seguridad_dc (default 1.25)
      - gauge por ampacidad y por vdrop (elige el mayor)
      - retorna gauge, vdrop
    """
    f_dc = _cfg_get(cfg_tecnicos, "factor_seguridad_dc", 1.25)
    vdrop_obj_dc = _cfg_get(cfg_tecnicos, "vdrop_obj_dc_pct", float(getattr(params, "vdrop_obj_dc_pct", 2.0)))

    base_i = float(isc_a) if isc_a is not None else float(imp_a)
    i_dc_diseno = float(base_i) * float(f_dc)

    g_amp = _pick_by_ampacity(AMP_PV_90C, i_dc_diseno, GAUGES_PV)
    g_vd = _pick_by_vdrop(float(vmp_string_v), float(imp_a), float(params.dist_dc_m), float(vdrop_obj_dc), GAUGES_PV)
    g_dc = _max_gauge(g_amp, g_vd, GAUGES_PV)

    vd_dc = _vdrop_pct_2wire(float(vmp_string_v), float(imp_a), float(params.dist_dc_m), g_dc)

    return {
        "gauge_awg": g_dc,
        "vdrop_pct": round(vd_dc, 2),
        "vdrop_obj_pct": float(vdrop_obj_dc),
        "i_diseno_a": float(i_dc_diseno),
        "factor_seguridad": float(f_dc),
    }


def _texto_pdf(
    *,
    params: ParametrosCableado,
    ac: Dict[str, Any],
    dc: Dict[str, Any],
) -> List[str]:
    ac_line = (
        f"Conductores AC (salida inversor): {ac['gauge_awg']} AWG Cu THHN/THWN-2 (L1+L2)"
        + (" + N" if params.incluye_neutro_ac else "")
        + f" + tierra {ac['tierra_awg']} AWG. Dist {params.dist_ac_m:.1f} m | caída {ac['vdrop_pct']:.2f}% "
          f"(obj {ac['vdrop_obj_pct']:.1f}%)."
    )

    dc_line = (
        f"Conductores DC (string): {dc['gauge_awg']} AWG Cu PV Wire/USE-2 (UV). Dist {params.dist_dc_m:.1f} m | "
        f"caída {dc['vdrop_pct']:.2f}% (obj {dc['vdrop_obj_pct']:.1f}%)."
    )

    return [
        dc_line,
        ac_line,
        f"Tubería AC sugerida: {ac['conduit']} EMT/PVC (según cantidad de conductores y facilidad de jalado).",
        f"Breaker AC sugerido (referencial): {ac['breaker_a']} A (validar contra datasheet del inversor).",
    ]


def _disclaimer() -> str:
    return (
        "Cálculo referencial para propuesta. Calibre final sujeto a: temperatura, agrupamiento (CCC), "
        "factor de ajuste/corrección, fill real de tubería, terminales 75°C y normativa local/NEC aplicable."
    )


# ==========================================================
# API pública
# ==========================================================

def calcular_cableado_referencial(
    *,
    params: ParametrosCableado,
    vmp_string_v: float,
    imp_a: float,
    isc_a: Optional[float],
    iac_estimado_a: float,
    cfg_tecnicos: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Retorna dict con recomendaciones DC/AC:
      - calibre por ampacidad y por caída (elige el mayor)
      - caída resultante
      - breaker y tubería sugerida (heurística)
      - texto_pdf: lista bullets
      - disclaimer

    cfg_tecnicos (opcional):
      - vdrop_obj_dc_pct, vdrop_obj_ac_pct
      - factor_seguridad_dc, factor_seguridad_ac
    """
    ac = _calcular_ac(params=params, iac_estimado_a=iac_estimado_a, cfg_tecnicos=cfg_tecnicos)
    dc = _calcular_dc(params=params, vmp_string_v=vmp_string_v, imp_a=imp_a, isc_a=isc_a, cfg_tecnicos=cfg_tecnicos)

    texto_pdf = _texto_pdf(params=params, ac=ac, dc=dc)

    return {
        "ac": {
            "gauge_awg": ac["gauge_awg"],
            "vdrop_pct": ac["vdrop_pct"],
            "breaker_a": ac["breaker_a"],
            "conduit": ac["conduit"],
            "tierra_awg": ac["tierra_awg"],
            "i_diseno_a": ac["i_diseno_a"],
            "vdrop_obj_pct": ac["vdrop_obj_pct"],
        },
        "dc": {
            "gauge_awg": dc["gauge_awg"],
            "vdrop_pct": dc["vdrop_pct"],
            "i_diseno_a": dc["i_diseno_a"],
            "vdrop_obj_pct": dc["vdrop_obj_pct"],
        },
        "texto_pdf": texto_pdf,
        "disclaimer": _disclaimer(),
    }
from typing import Any, Dict

def _ctx_nec(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "aplicar_derating": bool(d.get("aplicar_derating", True)),
        "t_amb_c": float(d.get("t_amb_c", d.get("temp_amb_c", 30.0))),
        "columna": str(d.get("columna_temp_nec", "75C")),
        "ccc_ac": int(d.get("ccc_ac", 3)),
        "ccc_dc": int(d.get("ccc_dc", 2)),
    }

def _post_dc(d: Dict[str, Any], dc: Dict[str, Any]) -> None:
    ns = int(dc.get("n_strings", 0))
    d["has_combiner"] = bool(d.get("has_combiner", ns >= 3))
    dc["config_strings"] = {"n_strings": ns, "modulos_por_string": int(d.get("n_modulos_serie", 0)),
                            "tipo": "string directo a inversor" if ns <= 2 else "con combiner box"}

from typing import Any, Dict

def _prep_d(datos: Dict[str, Any]):
    d = _defaults(datos)
    return d, _validar_minimos(d)

def _calc_dc_ac(d: Dict[str, Any]):
    s = parse_sistema_ac(d["tension_sistema"])
    dc = _calc_dc(d); _post_dc(d, dc)
    ac = _calc_ac(d, s)
    return s, dc, ac

def _compat_strings_en_sizing(d: Dict[str, Any], dc: Dict[str, Any]) -> None:
    d.setdefault("sizing", {}); d["sizing"].setdefault("cfg_strings", {})
    d["sizing"]["cfg_strings"]["strings"] = [{
        "mppt": 1, "n_series": int(d.get("n_modulos_serie", 0)), "n_paralelo": int(dc.get("n_strings", 0)),
        "vmp_string_v": dc.get("vmp_string_v", 0.0), "voc_string_frio_v": dc.get("voc_frio_string_v", 0.0),
        "imp_a": dc.get("i_string_oper_a", 0.0), "isc_a": dc.get("i_array_isc_a", 0.0),
    }]

def _ensamblar_paq(d: Dict[str, Any], s, dc: Dict[str, Any], ac: Dict[str, Any], warnings):
    ocpd = _calc_ocpd(d, dc, ac); cond = _calc_conductores_y_vd(d, s, dc, ac)
    paq = {"dc": dc, "ac": ac, "ocpd": ocpd, "conductores": cond, "spd": _recomendar_spd(d),
           "seccionamiento": _recomendar_seccionamiento(d), "canalizacion": _recomendar_canalizacion(cond),
           "warnings": warnings + dc.get("warnings", []) + ac.get("warnings", [])}
    paq["resumen_pdf"] = _armar_resumen_pdf(paq, s)
    return paq

def calcular_paquete_electrico_nec(datos: Dict[str, Any]) -> Dict[str, Any]:
    d, warnings = _prep_d(datos); d["nec"] = _ctx_nec(d)
    s, dc, ac = _calc_dc_ac(d); _compat_strings_en_sizing(d, dc)
    return _ensamblar_paq(d, s, dc, ac, warnings)

# ==========================================================
# Defaults + validación (corto y robusto)
# ==========================================================
def _defaults(d: Dict[str, Any]) -> Dict[str, Any]:
    x = dict(d or {})
    x.setdefault("tension_sistema", "2F+N_120/240")
    x.setdefault("pf_ac", 1.0)

    x.setdefault("vd_max_dc_pct", 2.0)
    x.setdefault("vd_max_ac_pct", 2.0)

    x.setdefault("material", "Cu")          # "Cu" o "Al"
    x.setdefault("temp_amb_c", 30.0)

    x.setdefault("L_dc_string_m", 10.0)
    x.setdefault("L_dc_trunk_m",  0.0)
    x.setdefault("L_ac_m", 15.0)

    x.setdefault("has_combiner", False)
    x.setdefault("dc_arch", "string_to_inverter")  # o "strings_to_combiner_to_inverter"
    return x


def _validar_minimos(d: Dict[str, Any]) -> List[str]:
    w: List[str] = []
    for k in ["n_strings", "isc_mod_a", "imp_mod_a", "vmp_string_v", "voc_frio_string_v", "p_ac_w"]:
        if d.get(k, None) is None:
            w.append(f"Falta '{k}' para ingeniería NEC.")
    return w


# ==========================================================
# Corrientes DC/AC
# ==========================================================
def _calc_dc(d: Dict[str, Any]) -> Dict[str, Any]:
    w: List[str] = []
    n = _as_int(d.get("n_strings", 0))
    isc = _as_float(d.get("isc_mod_a", 0.0))
    imp = _as_float(d.get("imp_mod_a", 0.0))
    vmp = _as_float(d.get("vmp_string_v", 0.0))
    voc = _as_float(d.get("voc_frio_string_v", 0.0))

    if n <= 0:
        w.append("n_strings <= 0, DC no calculable.")
    if isc <= 0 or imp <= 0:
        w.append("isc_mod_a/imp_mod_a inválidos.")
    if vmp <= 0 or voc <= 0:
        w.append("vmp_string_v/voc_frio_string_v inválidos.")

    i_string_oper = imp
    i_string_max = 1.25 * isc
    i_array_isc = n * isc
    i_array_design = 1.25 * i_array_isc

    return {
        "n_strings": n,
        "i_string_oper_a": round(i_string_oper, 3),
        "i_string_max_a": round(i_string_max, 3),
        "i_array_isc_a": round(i_array_isc, 3),
        "i_array_design_a": round(i_array_design, 3),
        "vmp_string_v": round(vmp, 2),
        "voc_frio_string_v": round(voc, 2),
        "warnings": w,
    }


def _calc_ac(d: Dict[str, Any], s: SistemaAC) -> Dict[str, Any]:
    w: List[str] = []
    p = _as_float(d.get("p_ac_w", 0.0))
    pf = _clamp(_as_float(d.get("pf_ac", 1.0)), 0.1, 1.0)

    if p <= 0:
        w.append("p_ac_w inválido (<=0).")

    i_nom = _iac(p, s.v_ll, pf, s.fases)
    i_design = 1.25 * i_nom

    return {
        "p_ac_w": round(p, 1),
        "pf": round(pf, 3),
        "v_ll_v": round(s.v_ll, 1),
        "fases": s.fases,
        "i_ac_nom_a": round(i_nom, 3),
        "i_ac_design_a": round(i_design, 3),
        "warnings": w,
    }


def _iac(p_w: float, v_ll: float, pf: float, fases: int) -> float:
    if v_ll <= 0 or pf <= 0:
        return 0.0
    if int(fases) == 3:
        return float(p_w) / (math.sqrt(3.0) * float(v_ll) * float(pf))
    return float(p_w) / (float(v_ll) * float(pf))


# ==========================================================
# OCPD (fusibles/breaker) — base referencial
# ==========================================================
def _calc_ocpd(d: Dict[str, Any], dc: Dict[str, Any], ac: Dict[str, Any]) -> Dict[str, Any]:
    fuse = _calc_fusible_string(d, dc)
    brk = _calc_breaker_ac(d, ac)
    return {"fusible_string": fuse, "breaker_ac": brk}


def _calc_fusible_string(d: Dict[str, Any], dc: Dict[str, Any]) -> Dict[str, Any]:
    n = int(dc.get("n_strings", 0))
    isc = _as_float(d.get("isc_mod_a", 0.0))
    req = bool(d.get("has_combiner", False)) and n >= 3
    i_min = 1.25 * isc

    if not req:
        return {"requerido": False, "nota": "Sin combiner o <3 strings en paralelo (verificar caso real)."}
    return {"requerido": True, "i_min_a": round(i_min, 2), "tamano_sugerido_a": _siguiente_ocpd(i_min)}


def _calc_breaker_ac(d: Dict[str, Any], ac: Dict[str, Any]) -> Dict[str, Any]:
    i_design = _as_float(ac.get("i_ac_design_a", 0.0))
    return {"i_design_a": round(i_design, 2), "tamano_sugerido_a": _siguiente_ocpd(i_design)}


def _siguiente_ocpd(a: float) -> int:
    std = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200]
    x = float(a)
    for s in std:
        if x <= s:
            return int(s)
    return int(std[-1])


# ==========================================================
# Conductores + caída de voltaje (modo referencial robusto)
# ==========================================================
def _calc_conductores_y_vd(d: Dict[str, Any], s: SistemaAC, dc: Dict[str, Any], ac: Dict[str, Any]) -> Dict[str, Any]:
    tab = _tabla_conductores_base(d.get("material", "Cu"))
    nec_base = d.get("nec", {})  # ✅ contexto NEC (si no existe, cae a {})

    dc_string = _tramo_conductor(
        nombre="DC string",
        i_a=_as_float(dc.get("i_string_max_a", 0.0)),
        v_base=_as_float(dc.get("vmp_string_v", 0.0)) or 600.0,
        l_m=_as_float(d.get("L_dc_string_m", 0.0)),
        vd_obj_pct=_as_float(d.get("vd_max_dc_pct", 2.0)),
        tabla=tab,
        n_hilos=2,
        nec={**nec_base, "ccc": int(nec_base.get("ccc_dc", 2))},
    )

    dc_trunk = None
    if bool(d.get("has_combiner", False)) and _as_float(d.get("L_dc_trunk_m", 0.0)) > 0:
        dc_trunk = _tramo_conductor(
            nombre="DC trunk",
            i_a=_as_float(dc.get("i_array_design_a", 0.0)),
            v_base=_as_float(dc.get("vmp_string_v", 0.0)) or 600.0,
            l_m=_as_float(d.get("L_dc_trunk_m", 0.0)),
            vd_obj_pct=_as_float(d.get("vd_max_dc_pct", 2.0)),
            tabla=tab,
            n_hilos=2,
            nec={**nec_base, "ccc": int(nec_base.get("ccc_dc", 2))},
        )

    ac_out = _tramo_conductor(
        nombre="AC salida inversor",
        i_a=_as_float(ac.get("i_ac_design_a", 0.0)),
        v_base=float(s.v_ll),
        l_m=_as_float(d.get("L_ac_m", 0.0)),
        vd_obj_pct=_as_float(d.get("vd_max_ac_pct", 2.0)),
        tabla=tab,
        n_hilos=2 if s.fases == 1 else 3,  # referencial (sin neutro explícito)
        nec={**nec_base, "ccc": int(nec_base.get("ccc_ac", 3))},
    )

    return {"dc_string": dc_string, "dc_trunk": dc_trunk, "ac_out": ac_out, "material": str(d.get("material", "Cu"))}

def _tramo_conductor(
    *,
    nombre: str,
    i_a: float,
    v_base: float,
    l_m: float,
    vd_obj_pct: float,
    tabla: List[Dict[str, Any]],
    n_hilos: int,
    nec: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if i_a <= 0 or l_m <= 0 or v_base <= 0:
        return {"nombre": nombre, "ok": False, "nota": "Datos insuficientes para conductor/VD."}

    t_amb_c = float((nec or {}).get("t_amb_c", 30.0))
    aplicar = bool((nec or {}).get("aplicar_derating", True))
    ccc = int((nec or {}).get("ccc", n_hilos))

    cand = _seleccionar_por_ampacidad_nec(i_a, tabla, t_amb_c=t_amb_c, ccc=ccc, aplicar=aplicar)
    best = _mejorar_por_vd(cand, i_a, v_base, l_m, vd_obj_pct, tabla, n_hilos=n_hilos)

    amp_adj, f_t, f_c = ampacidad_ajustada_nec(float(best["amp_a"]), t_amb_c, ccc, aplicar=aplicar)
    vd = _vdrop_pct(i_a, best["r_ohm_km"], l_m, v_base, n_hilos=n_hilos)

    return {
        "nombre": nombre, "ok": True,
        "i_a": round(float(i_a), 2), "l_m": round(float(l_m), 2), "v_base_v": round(float(v_base), 2),
        "awg": best["awg"], "amp_base_a": best["amp_a"],
        "amp_ajustada_a": round(float(amp_adj), 2), "fac_temp": round(float(f_t), 3), "fac_ccc": round(float(f_c), 3),
        "vd_pct": round(float(vd), 3), "vd_obj_pct": float(vd_obj_pct), "n_hilos": int(n_hilos),
    }

def _seleccionar_por_ampacidad(i_a: float, tabla: List[Dict[str, Any]]) -> Dict[str, Any]:
    x = float(i_a)
    for t in tabla:
        if x <= float(t["amp_a"]):
            return dict(t)
    return dict(tabla[-1])

def _seleccionar_por_ampacidad_nec(
    i_a: float,
    tabla: List[Dict[str, Any]],
    *,
    t_amb_c: float,
    ccc: int,
    aplicar: bool,
) -> Dict[str, Any]:
    x = float(i_a)
    ccc = max(1, int(ccc))
    for t in tabla:
        amp_adj, _, _ = ampacidad_ajustada_nec(float(t["amp_a"]), float(t_amb_c), ccc, aplicar=aplicar)
        if x <= amp_adj:
            return dict(t)
    return dict(tabla[-1])

def _mejorar_por_vd(
    cand: Dict[str, Any],
    i_a: float,
    v_base: float,
    l_m: float,
    vd_obj_pct: float,
    tabla: List[Dict[str, Any]],
    *,
    n_hilos: int,
) -> Dict[str, Any]:
    idx = _idx_awg(cand["awg"], tabla)
    while idx < len(tabla) - 1:
        vd = _vdrop_pct(i_a, tabla[idx]["r_ohm_km"], l_m, v_base, n_hilos=n_hilos)
        if vd <= float(vd_obj_pct):
            break
        idx += 1
    return dict(tabla[idx])


def _idx_awg(awg: str, tabla: List[Dict[str, Any]]) -> int:
    for i, t in enumerate(tabla):
        if str(t["awg"]) == str(awg):
            return i
    return 0


def _vdrop_pct(i_a: float, r_ohm_km: float, l_m: float, v_base: float, *, n_hilos: int = 2) -> float:
    r_total = float(r_ohm_km) * (float(l_m) / 1000.0) * float(n_hilos)
    vdrop = float(i_a) * r_total
    return 100.0 * (vdrop / float(v_base))


def _tabla_conductores_base(material: str) -> List[Dict[str, Any]]:
    # Referencial: R @20°C aprox + ampacidad base típica (ajustable luego por NEC 310/690)
    cu = [
        {"awg": "14",  "amp_a": 20,  "r_ohm_km": 8.286},
        {"awg": "12",  "amp_a": 25,  "r_ohm_km": 5.211},
        {"awg": "10",  "amp_a": 35,  "r_ohm_km": 3.277},
        {"awg": "8",   "amp_a": 50,  "r_ohm_km": 2.061},
        {"awg": "6",   "amp_a": 65,  "r_ohm_km": 1.296},
        {"awg": "4",   "amp_a": 85,  "r_ohm_km": 0.815},
        {"awg": "3",   "amp_a": 100, "r_ohm_km": 0.646},
        {"awg": "2",   "amp_a": 115, "r_ohm_km": 0.513},
        {"awg": "1",   "amp_a": 130, "r_ohm_km": 0.407},
        {"awg": "1/0", "amp_a": 150, "r_ohm_km": 0.323},
        {"awg": "2/0", "amp_a": 175, "r_ohm_km": 0.256},
        {"awg": "3/0", "amp_a": 200, "r_ohm_km": 0.203},
        {"awg": "4/0", "amp_a": 230, "r_ohm_km": 0.161},
    ]
    al = [
        {"awg": "12",  "amp_a": 20,  "r_ohm_km": 8.487},
        {"awg": "10",  "amp_a": 30,  "r_ohm_km": 5.350},
        {"awg": "8",   "amp_a": 40,  "r_ohm_km": 3.367},
        {"awg": "6",   "amp_a": 50,  "r_ohm_km": 2.118},
        {"awg": "4",   "amp_a": 65,  "r_ohm_km": 1.335},
        {"awg": "2",   "amp_a": 90,  "r_ohm_km": 0.840},
        {"awg": "1/0", "amp_a": 120, "r_ohm_km": 0.528},
        {"awg": "2/0", "amp_a": 135, "r_ohm_km": 0.418},
        {"awg": "3/0", "amp_a": 155, "r_ohm_km": 0.331},
        {"awg": "4/0", "amp_a": 180, "r_ohm_km": 0.263},
    ]
    return al if str(material).strip().upper() == "AL" else cu
