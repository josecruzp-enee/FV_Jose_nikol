# electrical/ingenieria_nec_2023.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from electrical.factores_nec import ampacidad_ajustada_nec
from electrical.protecciones import armar_ocpd
from electrical.tramos_base import caida_tension_pct, mejorar_por_vd as _mejorar_por_vd_base


# ==========================================================
# Modelos mínimos
# ==========================================================
@dataclass(frozen=True)
class SistemaAC:
    fases: int
    v_ll: float
    v_ln: Optional[float]
    tiene_neutro: bool


def parse_sistema_ac(tag: str) -> SistemaAC:
    m = _map_sistemas_ac()
    return m.get(str(tag), m["2F+N_120/240"])


def _map_sistemas_ac() -> Dict[str, SistemaAC]:
    return {
        "2F+N_120/240": SistemaAC(1, 240.0, 120.0, True),
        "3F+N_120/240": SistemaAC(3, 240.0, 120.0, True),
        "3F+N_120/208": SistemaAC(3, 208.0, 120.0, True),
        "3F_208Y120V":  SistemaAC(3, 208.0, 120.0, True),
        "3F_480Y277V":  SistemaAC(3, 480.0, 277.0, True),
    }


# ==========================================================
# Contexto NEC + orquestación
# ==========================================================
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
    dc["config_strings"] = {
        "n_strings": ns,
        "modulos_por_string": int(d.get("n_modulos_serie", 0)),
        "tipo": "string directo a inversor" if ns <= 2 else "con combiner box",
    }


def _prep_d(datos: Dict[str, Any]):
    d = _defaults(datos)
    return d, _validar_minimos(d)


def _calc_dc_ac(d: Dict[str, Any]):
    s = parse_sistema_ac(d["tension_sistema"])
    dc = _calc_dc(d)
    _post_dc(d, dc)
    ac = _calc_ac(d, s)
    return s, dc, ac


def _compat_strings_en_sizing(d: Dict[str, Any], dc: Dict[str, Any]) -> None:
    d.setdefault("sizing", {})
    d["sizing"].setdefault("cfg_strings", {})
    d["sizing"]["cfg_strings"]["strings"] = [{
        "mppt": 1,
        "n_series": int(d.get("n_modulos_serie", 0)),
        "n_paralelo": int(dc.get("n_strings", 0)),
        "vmp_string_v": dc.get("vmp_string_v", 0.0),
        "voc_string_frio_v": dc.get("voc_frio_string_v", 0.0),
        "imp_a": dc.get("i_string_oper_a", 0.0),
        "isc_a": dc.get("i_array_isc_a", 0.0),
    }]


def _ensamblar_paq(d: Dict[str, Any], s: SistemaAC, dc: Dict[str, Any], ac: Dict[str, Any], warnings: List[str]):
    # ✅ OCPD ahora viene del módulo electrical/protecciones.py (sin duplicar NEC aquí)
    ocpd = armar_ocpd(
        iac_nom_a=float(ac.get("i_ac_nom_a", 0.0)),
        n_strings=int(dc.get("n_strings", 0)),
        isc_mod_a=float(d.get("isc_mod_a", 0.0)),
        has_combiner=bool(d.get("has_combiner", False)),
    )

    cond = _calc_conductores_y_vd(d, s, dc, ac)
    paq = {
        "dc": dc,
        "ac": ac,
        "ocpd": ocpd,
        "conductores": cond,
        "spd": _recomendar_spd(d),
        "seccionamiento": _recomendar_seccionamiento(d),
        "canalizacion": _recomendar_canalizacion(cond),
        "warnings": warnings + dc.get("warnings", []) + ac.get("warnings", []),
    }
    paq["resumen_pdf"] = _armar_resumen_pdf(paq, s)
    return paq


def calcular_paquete_electrico_nec(datos: Dict[str, Any]) -> Dict[str, Any]:
    d, warnings = _prep_d(datos)
    d["nec"] = _ctx_nec(d)
    s, dc, ac = _calc_dc_ac(d)
    _compat_strings_en_sizing(d, dc)
    return _ensamblar_paq(d, s, dc, ac, warnings)


# ==========================================================
# Defaults + validación
# ==========================================================
def _defaults(d: Dict[str, Any]) -> Dict[str, Any]:
    x = dict(d or {})
    x.setdefault("tension_sistema", "2F+N_120/240")
    x.setdefault("pf_ac", 1.0)

    x.setdefault("vd_max_dc_pct", 2.0)
    x.setdefault("vd_max_ac_pct", 2.0)

    x.setdefault("material", "Cu")  # "Cu" o "Al"
    x.setdefault("temp_amb_c", 30.0)

    x.setdefault("L_dc_string_m", 10.0)
    x.setdefault("L_dc_trunk_m", 0.0)
    x.setdefault("L_ac_m", 15.0)

    x.setdefault("has_combiner", False)
    x.setdefault("dc_arch", "string_to_inverter")
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
# Conductores + caída de voltaje
# ==========================================================
def _calc_conductores_y_vd(d: Dict[str, Any], s: SistemaAC, dc: Dict[str, Any], ac: Dict[str, Any]) -> Dict[str, Any]:
    tab = _tabla_conductores_base(d.get("material", "Cu"))
    nec_base = d.get("nec", {})

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
        n_hilos=2 if s.fases == 1 else 3,
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
        "nombre": nombre,
        "ok": True,
        "i_a": round(float(i_a), 2),
        "l_m": round(float(l_m), 2),
        "v_base_v": round(float(v_base), 2),
        "awg": best["awg"],
        "amp_base_a": best["amp_a"],
        "amp_ajustada_a": round(float(amp_adj), 2),
        "fac_temp": round(float(f_t), 3),
        "fac_ccc": round(float(f_c), 3),
        "vd_pct": round(float(vd), 3),
        "vd_obj_pct": float(vd_obj_pct),
        "n_hilos": int(n_hilos),
    }


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


def _vdrop_pct(i_a: float, r_ohm_km: float, l_m: float, v_base: float, *, n_hilos: int = 2) -> float:
    return caida_tension_pct(v=float(v_base), i=float(i_a), l_m=float(l_m), r_ohm_km=float(r_ohm_km), n_hilos=int(n_hilos))


def _tabla_conductores_base(material: str) -> List[Dict[str, Any]]:
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


# ==========================================================
# SPD / seccionamiento / canalización
# ==========================================================
def _recomendar_spd(d: Dict[str, Any]) -> Dict[str, Any]:
    has_comb = bool(d.get("has_combiner", False))
    return {
        "dc": "Tipo 2 en entrada DC del inversor" + (" + Tipo 2 en combiner" if has_comb else ""),
        "ac": "Tipo 2 en tablero/POI (Tipo 1 si es en acometida/servicio)",
        "nota": "Seleccionar SPD por tensión (Vdc/Vac) e Imax/In según fabricante.",
    }


def _recomendar_seccionamiento(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "dc": "Desconectivo DC cercano al inversor (si no viene integrado).",
        "ac": "Desconectivo AC cercano al inversor o punto de interconexión (según práctica/local).",
    }


def _recomendar_canalizacion(conductores: Dict[str, Any]) -> Dict[str, Any]:
    def sug(n: int) -> str:
        if n <= 3:
            return '1/2"'
        if n <= 6:
            return '3/4"'
        if n <= 9:
            return '1"'
        return '1-1/4"'

    return {
        "dc_string": {"tuberia": sug(2), "nota": "2 conductores (±) referencial."},
        "dc_trunk":  {"tuberia": sug(2), "nota": "2 conductores (±) referencial."},
        "ac_out":    {"tuberia": sug(3), "nota": "L1/L2(+L3) referencial; agregar EGC/neutro si aplica."},
    }


# ==========================================================
# Resumen PDF
# ==========================================================
def _armar_resumen_pdf(paq: Dict[str, Any], s: SistemaAC) -> List[str]:
    dc = paq["conductores"]["dc_string"]
    ac = paq["conductores"]["ac_out"]
    fuse = (paq.get("ocpd") or {}).get("fusible_string", {}) or {}
    brk = (paq.get("ocpd") or {}).get("breaker_ac", {}) or {}

    brk_a = brk.get("tamano_sugerido_a") or brk.get("tamano_a") or 0
    fuse_a = fuse.get("tamano_sugerido_a") or fuse.get("tamano_a") or 0

    out: List[str] = []
    if dc.get("ok"):
        out.append(
            f"Conductores DC (string): {dc['awg']} {paq['conductores']['material']} | "
            f"Dist {dc['l_m']} m | caída {dc['vd_pct']}% (obj {dc['vd_obj_pct']}%)."
        )

    if paq["conductores"]["dc_trunk"] and paq["conductores"]["dc_trunk"].get("ok"):
        t = paq["conductores"]["dc_trunk"]
        out.append(
            f"Conductores DC (trunk): {t['awg']} {paq['conductores']['material']} | "
            f"Dist {t['l_m']} m | caída {t['vd_pct']}% (obj {t['vd_obj_pct']}%)."
        )

    if bool(fuse.get("requerido")):
        out.append(
            f"Fusible por string: mínimo {fuse.get('i_min_a', 0)} A | "
            f"sugerido {fuse_a} A (validar 'series fuse rating' del módulo)."
        )

    out.append(f"Corriente AC diseño: {paq['ac']['i_ac_design_a']} A @ {s.v_ll} V ({'3F' if s.fases==3 else '1F'}).")
    out.append(f"Breaker AC sugerido: {brk_a} A (según OCPD).")

    if ac.get("ok"):
        out.append(
            f"Conductores AC: {ac['awg']} {paq['conductores']['material']} | "
            f"Dist {ac['l_m']} m | caída {ac['vd_pct']}% (obj {ac['vd_obj_pct']}%)."
        )

    out.append("SPD: " + paq["spd"]["dc"] + " | " + paq["spd"]["ac"] + ".")
    out.append("Seccionamiento: " + paq["seccionamiento"]["dc"] + " | " + paq["seccionamiento"]["ac"] + ".")
    return out


# ==========================================================
# Utils
# ==========================================================
def _as_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def _as_int(x: Any) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))
