# reportes/presentacion_electrica.py
from __future__ import annotations
from typing import Any, Dict, List, Tuple

# ----------------------------
# Helpers
# ----------------------------

def _get(d: Any, path: str, default=None):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

def _first_dict(*cands):
    for x in cands:
        if isinstance(x, dict) and x:
            return x
    return {}

def _first_list(*cands):
    for x in cands:
        if isinstance(x, list) and x:
            return x
    return []

def _to_float(x: Any):
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None

def _fmt_num(x: Any, nd: int = 2) -> str:
    v = _to_float(x)
    if v is None:
        return "—"
    if nd == 0:
        return f"{v:,.0f}"
    return f"{v:,.{nd}f}"

def _fmt_val(value: Any, unit: str | None = None, nd: int = 2) -> str:
    s = _fmt_num(value, nd=nd) if isinstance(value, (int, float)) or _to_float(value) is not None else (str(value) if value not in (None, "") else "—")
    if s == "—":
        return s
    return f"{s} {unit}".strip() if unit else s

# ----------------------------
# Catálogo de labels bonitos
# ----------------------------

CATALOGO: Dict[str, Dict[str, str]] = {
    # DC
    "dc.n_strings": {
        "label": "Cantidad de strings",
        "help": "Número de ramales en paralelo del arreglo FV.",
    },
    "dc.modulos_por_string": {
        "label": "Módulos por string",
        "help": "Cantidad de módulos conectados en serie por string.",
    },
    "dc.vmp_string_v": {
        "label": "Vmp del string",
        "help": "Voltaje a potencia máxima (Vmp) del string a condiciones de operación.",
    },
    "dc.voc_frio_string_v": {
        "label": "Voc en frío",
        "help": "Voc corregido por temperatura mínima (condición crítica NEC para tensión).",
    },
    "dc.i_string_oper_a": {
        "label": "Corriente operativa del string",
        "help": "Corriente típica de operación del string.",
    },
    "dc.i_string_max_a": {
        "label": "Corriente máxima del string",
        "help": "Corriente máxima considerada para diseño.",
    },
    "dc.i_array_isc_a": {
        "label": "Isc del arreglo",
        "help": "Corriente de cortocircuito total del arreglo.",
    },
    "dc.i_array_design_a": {
        "label": "Corriente de diseño del arreglo",
        "help": "Corriente usada para dimensionamiento y protecciones según NEC.",
    },

    # AC
    "ac.p_ac_w": {
        "label": "Potencia AC",
        "help": "Potencia de salida AC considerada (normalmente potencia nominal del inversor).",
    },
    "ac.pf": {
        "label": "Factor de potencia (PF)",
        "help": "PF asumido para cálculo de corriente AC.",
    },
    "ac.v_ll_v": {
        "label": "Voltaje línea–línea",
        "help": "Voltaje L-L del sistema (trifásico) o equivalente según configuración.",
    },
    "ac.fases": {
        "label": "Número de fases",
        "help": "Monofásico / bifásico / trifásico.",
    },
    "ac.i_ac_nom_a": {
        "label": "Corriente nominal AC",
        "help": "Corriente calculada a potencia nominal y voltaje del sistema.",
    },
    "ac.i_ac_design_a": {
        "label": "Corriente de diseño AC",
        "help": "Corriente de diseño para conductor/breaker (criterio NEC).",
    },

    # Protecciones
    "prot.breaker_ac": {
        "label": "Breaker de salida AC",
        "help": "Tamaño recomendado del interruptor en salida del inversor.",
    },
    "prot.fusible_string": {
        "label": "Fusible por string",
        "help": "Requerimiento de fusible por string según paralelos/criterios de protección.",
    },

    # Conductores
    "cond.dc_string": {
        "label": "Conductor DC (string)",
        "help": "Calibre recomendado en el circuito DC del string considerando caída de tensión.",
    },
    "cond.ac_out": {
        "label": "Conductor AC (salida inversor)",
        "help": "Calibre recomendado en la salida AC considerando caída de tensión.",
    },
}

# ----------------------------
# Normalización
# ----------------------------

ddef normalizar_electrico(pkg: Dict[str, Any]) -> Dict[str, Any]:

    checks = {
        "ok_vdc": bool(pkg.get("ok_vdc", _get(pkg, "checks.ok_vdc", False))),
        "ok_mppt": bool(pkg.get("ok_mppt", _get(pkg, "checks.ok_mppt", False))),
        "ok_corriente": bool(pkg.get("ok_corriente", _get(pkg, "checks.ok_corriente", False))),
        "string_valido": bool(pkg.get("string_valido", _get(pkg, "checks.string_valido", False))),
    }

    # -------------------------
    # Corrientes
    # -------------------------
    dc = _first_dict(
        _get(pkg, "nec.dc"),
        _get(pkg, "corrientes_dc"),
        _get(pkg, "dc"),
        _get(pkg, "ingenieria.nec.dc"),
    )

    ac = _first_dict(
        _get(pkg, "nec.ac"),
        _get(pkg, "corrientes_ac"),
        _get(pkg, "ac"),
        _get(pkg, "ingenieria.nec.ac"),
    )

    # -------------------------
    # Protecciones (OCPD real NEC)
    # -------------------------
    protecciones = _first_dict(
        _get(pkg, "protecciones"),   # legacy
        _get(pkg, "ocpd"),           # ✅ contrato real motor NEC
        _get(pkg, "nec.protecciones"),
        _get(pkg, "proteccion"),
    )

    # -------------------------
    # SPD y Seccionamiento (NUEVO)
    # -------------------------
    spd = _first_dict(
        _get(pkg, "spd"),
        _get(pkg, "nec.spd"),
    )

    seccionamiento = _first_dict(
        _get(pkg, "seccionamiento"),
        _get(pkg, "nec.seccionamiento"),
    )

    # -------------------------
    # Conductores
    # -------------------------
    conductores = _first_dict(
        _get(pkg, "conductores"),
        _get(pkg, "nec.conductores"),
        _get(pkg, "cables"),
    )

    # -------------------------
    # Warnings
    # -------------------------
    warnings: List[str] = []
    warnings += list(_first_list(pkg.get("warnings"), _get(pkg, "texto_ui.checks")))
    warnings += list(_first_list(_get(dc, "warnings"), _get(ac, "warnings")))

    fus = _get(protecciones, "fusible_string", {})
    if isinstance(fus, dict) and fus.get("nota"):
        warnings.append(str(fus.get("nota")))

    warnings = [str(w) for w in warnings if str(w).strip()]

    # -------------------------
    # CONTRATO NORMALIZADO
    # -------------------------
    return {
        "checks": checks,
        "dc": dc or {},
        "ac": ac or {},
        "protecciones": protecciones or {},
        "spd": spd or {},                 # ✅ ahora visible en UI/PDF
        "seccionamiento": seccionamiento or {},  # ✅ nuevo
        "conductores": conductores or {},
        "warnings": warnings,
    }
def resumen_semáforo(norm: Dict[str, Any]) -> Tuple[str, str]:
    c = norm.get("checks") or {}
    ok_all = all(bool(c.get(k)) for k in ["ok_vdc", "ok_mppt", "ok_corriente", "string_valido"])
    if ok_all:
        return ("ok", "Validación eléctrica: TODO OK ✅")
    return ("warn", "Validación eléctrica: REVISAR ⚠️")

# ----------------------------
# NUEVO: items ricos (UI/PDF)
# ----------------------------

def items_dc(norm: Dict[str, Any]) -> List[Dict[str, Any]]:
    dc = norm.get("dc") or {}
    cfg = dc.get("config_strings") or {}
    return [
        _item("dc.n_strings", dc.get("n_strings", cfg.get("n_strings")), unit=None, nd=0),
        _item("dc.modulos_por_string", cfg.get("modulos_por_string"), unit=None, nd=0),
        _item("dc.vmp_string_v", dc.get("vmp_string_v"), unit="V", nd=1),
        _item("dc.voc_frio_string_v", dc.get("voc_frio_string_v"), unit="V", nd=1),
        _item("dc.i_string_oper_a", dc.get("i_string_oper_a"), unit="A", nd=2),
        _item("dc.i_string_max_a", dc.get("i_string_max_a"), unit="A", nd=2),
        _item("dc.i_array_isc_a", dc.get("i_array_isc_a"), unit="A", nd=2),
        _item("dc.i_array_design_a", dc.get("i_array_design_a"), unit="A", nd=3),
        {
            "key": "dc.tipo",
            "label": "Topología",
            "value": cfg.get("tipo", "—"),
            "unit": None,
            "help": "Tipo/configuración de strings (p. ej., serie/paralelo según tu modelo).",
        },
    ]

def items_ac(norm: Dict[str, Any]) -> List[Dict[str, Any]]:
    ac = norm.get("ac") or {}
    return [
        _item("ac.p_ac_w", ac.get("p_ac_w"), unit="W", nd=0),
        _item("ac.pf", ac.get("pf"), unit=None, nd=2),
        _item("ac.v_ll_v", ac.get("v_ll_v"), unit="V", nd=0),
        {"key": "ac.fases", "label": CATALOGO["ac.fases"]["label"], "value": ac.get("fases", "—"), "unit": None, "help": CATALOGO["ac.fases"]["help"]},
        _item("ac.i_ac_nom_a", ac.get("i_ac_nom_a"), unit="A", nd=2),
        _item("ac.i_ac_design_a", ac.get("i_ac_design_a"), unit="A", nd=2),
    ]

def items_protecciones(norm: Dict[str, Any]) -> List[Dict[str, Any]]:
    p = norm.get("protecciones") or {}
    br = p.get("breaker_ac") or {}
    fs = p.get("fusible_string") or {}

    breaker_txt = "—"
    if br:
        breaker_txt = f"{br.get('tamano_a', '—')} A (I diseño { _fmt_num(br.get('i_diseno_a')) } A)"

    fusible_txt = "Requerido" if bool(fs.get("requerido")) else "No requerido"
    nota = fs.get("nota", "—")

    return [
        {"key": "prot.breaker_ac", "label": CATALOGO["prot.breaker_ac"]["label"], "value": breaker_txt, "unit": None, "help": CATALOGO["prot.breaker_ac"]["help"]},
        {"key": "prot.fusible_string", "label": CATALOGO["prot.fusible_string"]["label"], "value": fusible_txt, "unit": None, "help": CATALOGO["prot.fusible_string"]["help"]},
        {"key": "prot.fusible_nota", "label": "Nota/criterio", "value": nota, "unit": None, "help": "Observación del criterio usado para el fusible."},
    ]

def items_conductores(norm: Dict[str, Any]) -> List[Dict[str, Any]]:
    c = norm.get("conductores") or {}
    dc = c.get("dc_string") or {}
    ac = c.get("ac_out") or {}
    mat = c.get("material", "—")

    items: List[Dict[str, Any]] = []
    if dc:
        items.append({
            "key": "cond.dc_string",
            "label": CATALOGO["cond.dc_string"]["label"],
            "value": {
                "circuito": "DC string",
                "awg": dc.get("awg", "—"),
                "i_a": dc.get("i_a"),
                "l_m": dc.get("l_m"),
                "vd_pct": dc.get("vd_pct"),
                "vd_obj_pct": dc.get("vd_obj_pct"),
                "material": mat,
                "ok": bool(dc.get("ok", True)),
            },
            "unit": None,
            "help": CATALOGO["cond.dc_string"]["help"],
        })
    if ac:
        items.append({
            "key": "cond.ac_out",
            "label": CATALOGO["cond.ac_out"]["label"],
            "value": {
                "circuito": "AC salida inversor",
                "awg": ac.get("awg", "—"),
                "i_a": ac.get("i_a"),
                "l_m": ac.get("l_m"),
                "vd_pct": ac.get("vd_pct"),
                "vd_obj_pct": ac.get("vd_obj_pct"),
                "material": mat,
                "ok": bool(ac.get("ok", True)),
            },
            "unit": None,
            "help": CATALOGO["cond.ac_out"]["help"],
        })
    return items

def _item(key: str, value: Any, unit: str | None, nd: int = 2) -> Dict[str, Any]:
    meta = CATALOGO.get(key, {})
    return {
        "key": key,
        "label": meta.get("label", key),
        "value": value,
        "unit": unit,
        "help": meta.get("help", ""),
        "nd": nd,
        "value_fmt": _fmt_val(value, unit=unit, nd=nd),
    }

# ----------------------------
# LEGACY: tus filas planas (para no romper)
# ----------------------------

def filas_dc(norm: Dict[str, Any]) -> List[List[str]]:
    return [[it["label"] + (f" ({it['unit']})" if it.get("unit") else ""), it.get("value_fmt", "—")] for it in items_dc(norm)]

def filas_ac(norm: Dict[str, Any]) -> List[List[str]]:
    return [[it["label"] + (f" ({it['unit']})" if it.get("unit") else ""), it.get("value_fmt", "—")] for it in items_ac(norm)]

def items_protecciones(norm: Dict[str, Any]) -> List[Dict[str, Any]]:

    p = norm.get("protecciones") or {}
    spd = norm.get("spd") or {}
    sec = norm.get("seccionamiento") or {}

    br = p.get("breaker_ac") or {}
    fs = p.get("fusible_string") or {}

    items: List[Dict[str, Any]] = []

    # =====================
    # PROTECCIONES DC
    # =====================
    items.append({
        "label": "— Protecciones DC —",
        "value": ""
    })

    items.append({
        "label": "Fusible por string",
        "value": "Requerido" if bool(fs.get("requerido")) else "No requerido"
    })

    if fs.get("nota"):
        items.append({
            "label": "Nota fusible",
            "value": fs.get("nota")
        })

    if spd.get("dc"):
        items.append({
            "label": "SPD DC",
            "value": spd.get("dc")
        })

    if sec.get("dc"):
        items.append({
            "label": "Seccionamiento DC",
            "value": sec.get("dc")
        })

    # =====================
    # PROTECCIONES AC
    # =====================
    items.append({
        "label": "— Protecciones AC —",
        "value": ""
    })

    breaker_txt = "—"
    if br:
        breaker_txt = f"{br.get('tamano_a','—')} A (I diseño { _to_num(br.get('i_diseno_a')) } A)"

    items.append({
        "label": "Breaker AC",
        "value": breaker_txt
    })

    if spd.get("ac"):
        items.append({
            "label": "SPD AC",
            "value": spd.get("ac")
        })

    if sec.get("ac"):
        items.append({
            "label": "Seccionamiento AC",
            "value": sec.get("ac")
        })

    return items
def filas_conductores(norm: Dict[str, Any]) -> List[List[str]]:
    # mantiene tu tabla ancha
    rows: List[List[str]] = []
    for it in items_conductores(norm):
        v = it["value"] or {}
        rows.append([
            v.get("circuito", "—"),
            str(v.get("awg", "—")),
            _fmt_val(v.get("i_a"), "A", nd=2),
            _fmt_val(v.get("l_m"), "m", nd=0),
            _fmt_val(v.get("vd_pct"), "%", nd=2),
            _fmt_val(v.get("vd_obj_pct"), "%", nd=2),
            str(v.get("material", "—")),
            "OK" if bool(v.get("ok", True)) else "REVISAR",
        ])
    return rows
