# Motor del dominio paneles/strings: ecuaciones FV para recomendar Ns/Np, validar voltajes y corrientes "a norma".
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor
from typing import Any, Dict, List, Optional


# Modelo de especificación del panel (contrato interno estable para el motor).
@dataclass(frozen=True)
class PanelSpec:
    pmax_w: float
    vmp_v: float
    voc_v: float
    imp_a: float
    isc_a: float
    coef_voc_pct_c: float  # %/°C (típicamente negativo)
    coef_vmp_pct_c: float = -0.34  # %/°C (típicamente negativo)


# Modelo de especificación del inversor (contrato interno estable para el motor).
@dataclass(frozen=True)
class InversorSpec:
    pac_kw: float
    vdc_max_v: float
    mppt_min_v: float
    mppt_max_v: float
    n_mppt: int
    imppt_max_a: float


# Convierte cualquier valor a float seguro.
def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


# Convierte cualquier valor a entero seguro.
def _i(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return int(default)


# Calcula Voc del módulo a Tmin para verificar Vdc_max del inversor.
def _voc_frio(*, voc_stc: float, coef_voc_pct_c: float, t_min_c: float, t_stc_c: float = 25.0) -> float:
    return float(voc_stc) * (1.0 + (float(coef_voc_pct_c) / 100.0) * (float(t_min_c) - float(t_stc_c)))


# Calcula Vmp del módulo a temperatura operativa para verificar MPPT_min del inversor.
def _vmp_temp(*, vmp_stc: float, coef_vmp_pct_c: float, t_oper_c: float, t_stc_c: float = 25.0) -> float:
    return float(vmp_stc) * (1.0 + (float(coef_vmp_pct_c) / 100.0) * (float(t_oper_c) - float(t_stc_c)))


# Calcula límites n_min/n_max de módulos en serie por Vdc_max y ventana MPPT.
def _bounds_por_voltaje(*, panel: PanelSpec, inv: InversorSpec, t_min_c: float, t_oper_c: float) -> Dict[str, Any]:
    voc_frio_panel_v = _voc_frio(voc_stc=panel.voc_v, coef_voc_pct_c=panel.coef_voc_pct_c, t_min_c=t_min_c)
    vmp_hot_panel_v = _vmp_temp(vmp_stc=panel.vmp_v, coef_vmp_pct_c=panel.coef_vmp_pct_c, t_oper_c=t_oper_c)

    max_por_vdc = floor(inv.vdc_max_v / max(voc_frio_panel_v, 1e-9))
    min_por_mppt = ceil(inv.mppt_min_v / max(vmp_hot_panel_v, 1e-9))
    max_por_mppt = floor(inv.mppt_max_v / max(panel.vmp_v, 1e-9))

    n_min = max(1, int(min_por_mppt))
    n_max = max(0, int(min(max_por_vdc, max_por_mppt)))

    return {
        "voc_frio_panel_v": float(voc_frio_panel_v),
        "vmp_hot_panel_v": float(vmp_hot_panel_v),
        "t_oper_c": float(t_oper_c),
        "n_min": int(n_min),
        "n_max": int(n_max),
        "max_por_vdc": int(max_por_vdc),
        "min_por_mppt": int(min_por_mppt),
        "max_por_mppt": int(max_por_mppt),
    }


# Puntúa un candidato Ns para acercar Vmp_hot al centro de la ventana MPPT.
def _score_n(*, n_series: int, panel: PanelSpec, inv: InversorSpec, t_oper_c: float) -> float:
    vmp_hot_panel = _vmp_temp(vmp_stc=panel.vmp_v, coef_vmp_pct_c=panel.coef_vmp_pct_c, t_oper_c=t_oper_c)
    vmp_string_hot = int(n_series) * vmp_hot_panel
    mid = (inv.mppt_min_v + inv.mppt_max_v) / 2.0
    return abs(vmp_string_hot - mid)


# Divide la cantidad de strings entre MPPT según topología (1-agua / 2-aguas).
def _split_por_mppt(*, n_strings_total: int, n_mppt: int, dos_aguas: bool) -> List[Dict[str, Any]]:
    if n_strings_total <= 0:
        return []
    if bool(dos_aguas) and n_mppt >= 2:
        s1 = n_strings_total // 2
        s2 = n_strings_total - s1
        ramas = [
            {"mppt": 1, "n_strings": s1, "etiqueta": "Techo izquierdo"},
            {"mppt": 2, "n_strings": s2, "etiqueta": "Techo derecho"},
        ]
        return [r for r in ramas if r["n_strings"] > 0]
    return [{"mppt": 1, "n_strings": int(n_strings_total), "etiqueta": "Arreglo FV"}]


# Recomienda Ns y número total de strings en función de límites eléctricos y objetivo DC.
def recomendar_string(
    *,
    panel: PanelSpec,
    inversor: InversorSpec,
    t_min_c: float,
    objetivo_dc_ac: float,
    pdc_kw_objetivo: Optional[float] = None,
    t_oper_c: float = 55.0,
) -> Dict[str, Any]:
    errores: List[str] = []
    warnings: List[str] = []

    if inversor.n_mppt <= 0:
        errores.append("Inversor inválido: n_mppt <= 0.")
    if panel.pmax_w <= 0 or panel.vmp_v <= 0 or panel.voc_v <= 0:
        errores.append("Panel inválido: revisar STC (pmax/vmp/voc).")

    if errores:
        return {"ok": False, "errores": errores, "warnings": warnings, "bounds": {}, "recomendacion": {}}

    bounds = _bounds_por_voltaje(panel=panel, inv=inversor, t_min_c=float(t_min_c), t_oper_c=float(t_oper_c))
    n_min, n_max = int(bounds["n_min"]), int(bounds["n_max"])

    if n_max < n_min:
        errores.append(
            f"No existe N válido: n_min={n_min}, n_max={n_max}. "
            f"Revisa MPPT o Vdc_max vs Voc frío / Vmp caliente."
        )
        return {"ok": False, "errores": errores, "warnings": warnings, "bounds": bounds, "recomendacion": {}}

    candidatos = list(range(n_min, n_max + 1))
    n_series = min(candidatos, key=lambda n: _score_n(n_series=n, panel=panel, inv=inversor, t_oper_c=float(t_oper_c)))

    pdc_obj_kw = float(pdc_kw_objetivo) if pdc_kw_objetivo is not None else (float(objetivo_dc_ac) * float(inversor.pac_kw))
    pdc_obj_w = pdc_obj_kw * 1000.0

    p_string_w = float(n_series) * float(panel.pmax_w)
    n_strings_total = max(1, int(ceil(pdc_obj_w / max(p_string_w, 1e-9))))

    vmp_hot_panel_v = float(bounds["vmp_hot_panel_v"])
    vmp_hot_string_v = vmp_hot_panel_v * float(n_series)
    vmp_stc_string_v = float(panel.vmp_v) * float(n_series)

    voc_frio_panel_v = float(bounds["voc_frio_panel_v"])
    voc_frio_string_v = voc_frio_panel_v * float(n_series)

    if voc_frio_string_v > inversor.vdc_max_v + 1e-9:
        errores.append(f"Voc frío string excede Vdc_max: {voc_frio_string_v:.1f} V > {inversor.vdc_max_v:.1f} V")

    if vmp_hot_string_v < inversor.mppt_min_v - 1e-9:
        errores.append(
            f"Vmp caliente por debajo de MPPT_min: {vmp_hot_string_v:.1f} V < {inversor.mppt_min_v:.1f} V "
            f"(T_oper≈{float(t_oper_c):.0f}°C)."
        )

    if vmp_stc_string_v > inversor.mppt_max_v + 1e-9:
        warnings.append(f"Vmp STC por encima de MPPT_max (referencial): {vmp_stc_string_v:.1f} V > {inversor.mppt_max_v:.1f} V.")

    return {
        "ok": len(errores) == 0,
        "errores": errores,
        "warnings": warnings,
        "bounds": bounds,
        "recomendacion": {
            "n_series": int(n_series),
            "n_strings_total": int(n_strings_total),
            "pdc_obj_kw": float(pdc_obj_kw),
            "p_string_kw_stc": float(p_string_w / 1000.0),
            "vmp_string_v": float(vmp_hot_string_v),          # Vmp caliente
            "vmp_stc_string_v": float(vmp_stc_string_v),      # trazabilidad
            "voc_frio_string_v": float(voc_frio_string_v),
            "t_oper_c": float(t_oper_c),
        },
    }


# Ejecuta el motor de strings: recomienda Ns/Np, valida límites y retorna datos para siguientes dominios.
def calcular_strings_fv(
    *,
    n_paneles_total: int,
    panel: Any,
    inversor: Any,
    t_min_c: float,
    dos_aguas: bool = False,
    objetivo_dc_ac: float | None = None,
    pdc_kw_objetivo: float | None = None,
    t_oper_c: float | None = None,
) -> Dict[str, Any]:
    errores: List[str] = []
    warnings: List[str] = []

    n_total = _i(n_paneles_total, 0)
    if n_total <= 0:
        return {"ok": False, "errores": ["n_paneles_total inválido (<=0)."], "warnings": [], "topologia": "N/A", "bounds": {}, "recomendacion": {}, "strings": [], "meta": {}}

    try:
        tmin = float(t_min_c)
    except Exception:
        return {"ok": False, "errores": ["t_min_c inválido (no convertible a número)."], "warnings": [], "topologia": "N/A", "bounds": {}, "recomendacion": {}, "strings": [], "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas)}}

    if not isinstance(panel, PanelSpec) or not isinstance(inversor, InversorSpec):
        return {"ok": False, "errores": ["calcular_strings_fv requiere PanelSpec e InversorSpec (normaliza en orquestador)."], "warnings": [], "topologia": "N/A", "bounds": {}, "recomendacion": {}, "strings": [], "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas), "t_min_c": tmin}}

    p: PanelSpec = panel
    inv: InversorSpec = inversor

    if inv.n_mppt <= 0:
        errores.append("Inversor inválido: n_mppt <= 0.")
    if p.pmax_w <= 0 or p.vmp_v <= 0 or p.voc_v <= 0:
        errores.append("Panel inválido: pmax/vmp/voc deben ser > 0.")
    if inv.vdc_max_v <= 0 or inv.mppt_min_v <= 0 or inv.mppt_max_v <= 0:
        errores.append("Inversor inválido: vdc_max/mppt_min/mppt_max deben ser > 0.")
    if inv.mppt_min_v >= inv.mppt_max_v:
        errores.append("Inversor inválido: mppt_min_v debe ser < mppt_max_v.")
    if inv.imppt_max_a <= 0:
        errores.append("Inversor inválido: imppt_max_a debe ser > 0.")

    if errores:
        return {"ok": False, "errores": errores, "warnings": warnings, "topologia": "N/A", "bounds": {}, "recomendacion": {}, "strings": [], "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas), "t_min_c": tmin}}

    t_oper = float(t_oper_c) if t_oper_c is not None else 55.0

    rec = recomendar_string(
        panel=p,
        inversor=inv,
        t_min_c=tmin,
        objetivo_dc_ac=float(objetivo_dc_ac) if objetivo_dc_ac is not None else 1.2,
        pdc_kw_objetivo=float(pdc_kw_objetivo) if pdc_kw_objetivo is not None else None,
        t_oper_c=t_oper,
    )

    if not rec.get("ok", False):
        return {
            "ok": False,
            "errores": list(rec.get("errores") or ["No se pudo recomendar string."]),
            "warnings": list(rec.get("warnings") or []),
            "topologia": "N/A",
            "bounds": rec.get("bounds") or {},
            "recomendacion": rec.get("recomendacion") or {},
            "strings": [],
            "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas), "t_min_c": tmin, "t_oper_c": float(t_oper)},
        }

    r = rec.get("recomendacion") or {}

    n_series = _i(r.get("n_series"), 0)
    if n_series <= 0:
        return {
            "ok": False,
            "errores": ["recomendar_string no retornó n_series válido."],
            "warnings": list(rec.get("warnings") or []),
            "topologia": "N/A",
            "bounds": rec.get("bounds") or {},
            "recomendacion": r,
            "strings": [],
            "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas), "t_min_c": tmin, "t_oper_c": float(t_oper)},
        }

    n_strings_total = _i(r.get("n_strings_total"), 0)
    if n_strings_total <= 0:
        n_strings_total = max(1, int(ceil(n_total / max(n_series, 1))))

    topologia = "2-aguas" if (bool(dos_aguas) and inv.n_mppt >= 2) else "1-agua"
    ramas = _split_por_mppt(n_strings_total=n_strings_total, n_mppt=inv.n_mppt, dos_aguas=bool(dos_aguas))

    strings: List[Dict[str, Any]] = []
    errores_mppt: List[str] = []

    for rama in ramas:
        mppt = int(rama["mppt"])
        n_paralelo = int(rama["n_strings"])
        etiqueta = str(rama.get("etiqueta") or "Arreglo FV")

        isc_array_a = float(p.isc_a) * float(n_paralelo)
        imax_pv_a = 1.25 * isc_array_a
        idesign_cont_a = 1.56 * isc_array_a

        if imax_pv_a > inv.imppt_max_a + 1e-9:
            errores_mppt.append(
                f"Corriente máxima FV excede límite MPPT {mppt}: "
                f"1.25×Isc_array={imax_pv_a:.2f} A > Imppt_max={inv.imppt_max_a:.2f} A."
            )

        i_mppt_oper_a = float(p.imp_a) * float(n_paralelo)

        strings.append(
            {
                "mppt": mppt,
                "etiqueta": etiqueta,
                "n_series": int(n_series),
                "n_paralelo": int(n_paralelo),
                "vmp_string_v": float(r.get("vmp_string_v") or 0.0),
                "vmp_stc_string_v": float(r.get("vmp_stc_string_v") or 0.0),
                "voc_frio_string_v": float(r.get("voc_frio_string_v") or 0.0),
                "imp_a": float(p.imp_a),
                "isc_a": float(p.isc_a),
                "i_mppt_a": float(i_mppt_oper_a),
                "isc_array_a": float(isc_array_a),
                "imax_pv_a": float(imax_pv_a),
                "idesign_cont_a": float(idesign_cont_a),
            }
        )

    if errores_mppt:
        return {
            "ok": False,
            "errores": errores_mppt,
            "warnings": list(rec.get("warnings") or []),
            "topologia": topologia,
            "bounds": rec.get("bounds") or {},
            "recomendacion": rec.get("recomendacion") or {},
            "strings": strings,
            "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas), "n_mppt": int(inv.n_mppt), "t_min_c": float(tmin), "t_oper_c": float(t_oper)},
        }

    p_string_kw = float(r.get("p_string_kw_stc") or 0.0)
    pdc_total_kw = float(n_strings_total) * float(p_string_kw)
    dc_ac_real = (pdc_total_kw / float(inv.pac_kw)) if float(inv.pac_kw) > 1e-9 else 0.0

    recomendacion = {
        "n_series": int(n_series),
        "n_paneles_string": int(n_series),
        "n_strings_total": int(n_strings_total),
        "strings_por_mppt": int(ceil(n_strings_total / max(inv.n_mppt, 1))),
        "vmp_string_v": float(r.get("vmp_string_v") or 0.0),
        "vmp_stc_string_v": float(r.get("vmp_stc_string_v") or 0.0),
        "voc_frio_string_v": float(r.get("voc_frio_string_v") or 0.0),
        "pdc_obj_kw": float(r.get("pdc_obj_kw") or 0.0),
        "p_string_kw_stc": float(p_string_kw),
        "pdc_total_kw_stc": float(pdc_total_kw),
        "dc_ac_real": float(dc_ac_real),
        "t_oper_c": float(r.get("t_oper_c") or t_oper),
    }

    meta = {
        "n_paneles_total": int(n_total),
        "dos_aguas": bool(dos_aguas),
        "n_mppt": int(inv.n_mppt),
        "t_min_c": float(tmin),
        "t_oper_c": float(t_oper),
    }

    return {"ok": True, "errores": [], "warnings": list(rec.get("warnings") or []), "topologia": topologia, "bounds": rec.get("bounds") or {}, "recomendacion": recomendacion, "strings": strings, "meta": meta}


# Alias legado: mantener temporalmente hasta eliminar referencias en el repo.
calcular_strings_auto = calcular_strings_fv
