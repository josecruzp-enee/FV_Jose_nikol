# reportes/presentacion_electrica.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _get(d: Any, path: str, default=None):
    """
    Acceso tolerante: path tipo "a.b.c" sobre dicts.
    """
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


def normalizar_electrico(pkg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve un contrato único:
    {
      "checks": {"ok_vdc": bool, "ok_mppt": bool, "ok_corriente": bool, "string_valido": bool},
      "dc": {...},
      "ac": {...},
      "protecciones": {...},
      "conductores": {"dc_string": {...}, "ac_out": {...}},
      "warnings": [str, ...]
    }
    """
    checks = {
        "ok_vdc": bool(pkg.get("ok_vdc", _get(pkg, "checks.ok_vdc", False))),
        "ok_mppt": bool(pkg.get("ok_mppt", _get(pkg, "checks.ok_mppt", False))),
        "ok_corriente": bool(pkg.get("ok_corriente", pkg.get("ok_corriente", _get(pkg, "checks.ok_corriente", False)))),
        "string_valido": bool(pkg.get("string_valido", _get(pkg, "checks.string_valido", False))),
    }

    # DC: buscar en lugares comunes
    dc = _first_dict(
        _get(pkg, "nec.dc"),
        _get(pkg, "corrientes_dc"),
        _get(pkg, "dc"),
        _get(pkg, "ingenieria.nec.dc"),
    )

    # AC
    ac = _first_dict(
        _get(pkg, "nec.ac"),
        _get(pkg, "corrientes_ac"),
        _get(pkg, "ac"),
        _get(pkg, "ingenieria.nec.ac"),
    )

    # Protecciones
    protecciones = _first_dict(
        _get(pkg, "protecciones"),
        _get(pkg, "nec.protecciones"),
        _get(pkg, "proteccion"),
    )

    # Conductores
    conductores = _first_dict(
        _get(pkg, "conductores"),
        _get(pkg, "nec.conductores"),
        _get(pkg, "cables"),
    )

    # Warnings (juntar de varias fuentes típicas)
    warnings = []
    warnings += list(_first_list(pkg.get("warnings"), _get(pkg, "texto_ui.checks")))
    warnings += list(_first_list(_get(dc, "warnings"), _get(ac, "warnings")))
    # Protecciones y fusibles a veces traen nota
    fus = _get(protecciones, "fusible_string", {})
    if isinstance(fus, dict):
        nota = fus.get("nota")
        if nota:
            warnings.append(str(nota))

    # Sanitizar
    warnings = [str(w) for w in warnings if str(w).strip()]

    return {
        "checks": checks,
        "dc": dc or {},
        "ac": ac or {},
        "protecciones": protecciones or {},
        "conductores": conductores or {},
        "warnings": warnings,
    }


def resumen_semáforo(norm: Dict[str, Any]) -> Tuple[str, str]:
    """
    Retorna (nivel, mensaje) donde nivel ∈ {"ok","warn","fail"}
    """
    c = norm.get("checks") or {}
    ok_all = all(bool(c.get(k)) for k in ["ok_vdc", "ok_mppt", "ok_corriente", "string_valido"])
    if ok_all:
        return ("ok", "Validación eléctrica: TODO OK ✅")

    # si falla string o vdc/mppt/corriente -> warn
    return ("warn", "Validación eléctrica: REVISAR ⚠️")


def filas_dc(norm: Dict[str, Any]) -> List[List[str]]:
    dc = norm.get("dc") or {}
    cfg = dc.get("config_strings") or {}
    return [
        ["Número de strings", f"{dc.get('n_strings', cfg.get('n_strings', '—'))}"],
        ["Módulos por string", f"{cfg.get('modulos_por_string', '—')}"],
        ["Vmp string (V)", f"{_to_num(dc.get('vmp_string_v'))}"],
        ["Voc frío string (V)", f"{_to_num(dc.get('voc_frio_string_v'))}"],
        ["I string operativa (A)", f"{_to_num(dc.get('i_string_oper_a'))}"],
        ["I string máx diseño (A)", f"{_to_num(dc.get('i_string_max_a'))}"],
        ["Isc arreglo (A)", f"{_to_num(dc.get('i_array_isc_a'))}"],
        ["I diseño arreglo (A)", f"{_to_num(dc.get('i_array_design_a'))}"],
        ["Tipo", f"{cfg.get('tipo', '—')}"],
    ]


def filas_ac(norm: Dict[str, Any]) -> List[List[str]]:
    ac = norm.get("ac") or {}
    return [
        ["Potencia AC (W)", f"{_to_num(ac.get('p_ac_w'), 0)}"],
        ["PF", f"{_to_num(ac.get('pf'))}"],
        ["V L-L (V)", f"{_to_num(ac.get('v_ll_v'), 0)}"],
        ["Fases", f"{ac.get('fases', '—')}"],
        ["I AC nominal (A)", f"{_to_num(ac.get('i_ac_nom_a'))}"],
        ["I AC diseño (A)", f"{_to_num(ac.get('i_ac_design_a'))}"],
    ]


def filas_protecciones(norm: Dict[str, Any]) -> List[List[str]]:
    p = norm.get("protecciones") or {}
    br = p.get("breaker_ac") or {}
    fs = p.get("fusible_string") or {}
    return [
        ["Breaker AC (A)", f"{br.get('tamano_a', '—')} (Idiseño { _to_num(br.get('i_diseno_a')) } A)"],
        ["Fusible string", f"{'Requerido' if bool(fs.get('requerido')) else 'No requerido'}"],
        ["Nota fusible", f"{fs.get('nota','—')}"],
    ]


def filas_conductores(norm: Dict[str, Any]) -> List[List[str]]:
    c = norm.get("conductores") or {}
    dc = c.get("dc_string") or {}
    ac = c.get("ac_out") or {}
    mat = c.get("material", "—")

    rows = []
    if dc:
        rows.append([
            "DC string",
            str(dc.get("awg", "—")),
            f"{_to_num(dc.get('i_a'))}",
            f"{_to_num(dc.get('l_m'), 0)}",
            f"{_to_num(dc.get('vd_pct'))}%",
            f"{_to_num(dc.get('vd_obj_pct'))}%",
            mat,
            "OK" if bool(dc.get("ok", True)) else "REVISAR",
        ])
    if ac:
        rows.append([
            "AC salida inversor",
            str(ac.get("awg", "—")),
            f"{_to_num(ac.get('i_a'))}",
            f"{_to_num(ac.get('l_m'), 0)}",
            f"{_to_num(ac.get('vd_pct'))}%",
            f"{_to_num(ac.get('vd_obj_pct'))}%",
            mat,
            "OK" if bool(ac.get("ok", True)) else "REVISAR",
        ])
    return rows


def _to_num(x: Any, nd: int = 2) -> str:
    try:
        if x is None:
            return "—"
        v = float(x)
        fmt = f"{{:,.{nd}f}}"
        # si nd=0
        if nd == 0:
            fmt = "{:,.0f}"
        return fmt.format(v)
    except Exception:
        return str(x) if x not in (None, "") else "—"
