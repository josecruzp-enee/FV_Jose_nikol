from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor
from typing import Any, Dict, List, Optional


# ==========================================================
# Modelos de especificación (contrato interno estable)
# ==========================================================
@dataclass(frozen=True)
class PanelSpec:
    pmax_w: float
    vmp_v: float
    voc_v: float
    imp_a: float
    isc_a: float
    coef_voc_pct_c: float  # ej -0.28 (%/°C)


@dataclass(frozen=True)
class InversorSpec:
    pac_kw: float
    vdc_max_v: float
    mppt_min_v: float
    mppt_max_v: float
    n_mppt: int
    imppt_max_a: float


# ==========================================================
# Utilitarios numéricos (internos)
# ==========================================================
def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _i(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return int(default)


# ==========================================================
# Cálculos base
# ==========================================================
def _voc_frio(
    *,
    voc_stc: float,
    coef_voc_pct_c: float,
    t_min_c: float,
    t_stc_c: float = 25.0,
) -> float:
    """
    Voc(T) = Voc_STC * (1 + coef%/°C/100 * (T - 25))
    coef_voc_pct_c es %/°C (normalmente negativo).
    """
    return float(voc_stc) * (1.0 + (float(coef_voc_pct_c) / 100.0) * (float(t_min_c) - float(t_stc_c)))


def _bounds_por_voltaje(*, panel: PanelSpec, inv: InversorSpec, t_min_c: float) -> Dict[str, Any]:
    voc_frio_panel_v = _voc_frio(voc_stc=panel.voc_v, coef_voc_pct_c=panel.coef_voc_pct_c, t_min_c=t_min_c)

    # Límite por Vdc max usando Voc frío por panel
    max_por_vdc = floor(inv.vdc_max_v / max(voc_frio_panel_v, 1e-9))

    # Límite por MPPT usando Vmp STC por panel como aproximación
    min_por_mppt = ceil(inv.mppt_min_v / max(panel.vmp_v, 1e-9))
    max_por_mppt = floor(inv.mppt_max_v / max(panel.vmp_v, 1e-9))

    n_min = max(1, int(min_por_mppt))
    n_max = max(0, int(min(max_por_vdc, max_por_mppt)))

    return {
        "voc_frio_panel_v": float(voc_frio_panel_v),
        "n_min": int(n_min),
        "n_max": int(n_max),
        "max_por_vdc": int(max_por_vdc),
        "min_por_mppt": int(min_por_mppt),
        "max_por_mppt": int(max_por_mppt),
    }


def _score_n(*, n_series: int, panel: PanelSpec, inv: InversorSpec) -> float:
    """Menor es mejor: Vmp_string cerca del centro de MPPT."""
    vmp_string = int(n_series) * panel.vmp_v
    mid = (inv.mppt_min_v + inv.mppt_max_v) / 2.0
    return abs(vmp_string - mid)


def _split_por_mppt(*, n_strings_total: int, n_mppt: int, dos_aguas: bool) -> List[Dict[str, Any]]:
    """
    Retorna lista de "ramas" por MPPT: [{mppt, n_strings}]
    Si dos_aguas True y hay >=2 MPPT, reparte en dos ramas (mppt 1 y 2).
    Si no, todo a mppt 1.
    """
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


# ==========================================================
# Recomendación base (N series + cantidad de strings)
# ==========================================================
def recomendar_string(
    *,
    panel: PanelSpec,
    inversor: InversorSpec,
    t_min_c: float,
    objetivo_dc_ac: float,
    pdc_kw_objetivo: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Recomienda (en base a límites eléctricos y objetivo DC):
      - n_series (paneles en serie)
      - n_strings_total
      - pdc_obj_kw, p_string_kw_stc
      - vmp_string_v, voc_frio_string_v (por string)
    """
    errores: List[str] = []
    warnings: List[str] = []

    if inversor.n_mppt <= 0:
        errores.append("Inversor inválido: n_mppt <= 0.")
    if panel.pmax_w <= 0 or panel.vmp_v <= 0 or panel.voc_v <= 0:
        errores.append("Panel inválido: revisar STC (pmax/vmp/voc).")

    if errores:
        return {"ok": False, "errores": errores, "warnings": warnings, "bounds": {}, "recomendacion": {}}

    bounds = _bounds_por_voltaje(panel=panel, inv=inversor, t_min_c=float(t_min_c))
    n_min, n_max = int(bounds["n_min"]), int(bounds["n_max"])

    if n_max < n_min:
        errores.append(
            f"No existe N válido: n_min={n_min}, n_max={n_max}. "
            f"Revisa MPPT o Vdc_max vs Voc frío."
        )
        return {"ok": False, "errores": errores, "warnings": warnings, "bounds": bounds, "recomendacion": {}}

    candidatos = list(range(n_min, n_max + 1))
    n_series = min(candidatos, key=lambda n: _score_n(n_series=n, panel=panel, inv=inversor))

    # Potencia DC objetivo
    pdc_obj_kw = float(pdc_kw_objetivo) if pdc_kw_objetivo is not None else (float(objetivo_dc_ac) * float(inversor.pac_kw))
    pdc_obj_w = pdc_obj_kw * 1000.0

    p_string_w = float(n_series) * float(panel.pmax_w)
    n_strings_total = max(1, int(ceil(pdc_obj_w / max(p_string_w, 1e-9))))

    # Voltajes del string
    vmp_string_v = float(panel.vmp_v) * float(n_series)
    voc_frio_panel_v = float(bounds["voc_frio_panel_v"])
    voc_frio_string_v = voc_frio_panel_v * float(n_series)

    # Checks (informativos)
    if voc_frio_string_v > inversor.vdc_max_v + 1e-9:
        errores.append(f"Voc frío string excede Vdc_max: {voc_frio_string_v:.1f} V > {inversor.vdc_max_v:.1f} V")

    if vmp_string_v < inversor.mppt_min_v - 1e-9 or vmp_string_v > inversor.mppt_max_v + 1e-9:
        warnings.append(
            f"Vmp string fuera de MPPT (referencial): {vmp_string_v:.1f} V vs "
            f"{inversor.mppt_min_v:.1f}-{inversor.mppt_max_v:.1f} V."
        )

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
            "vmp_string_v": float(vmp_string_v),
            "voc_frio_string_v": float(voc_frio_string_v),
        },
    }


# ==========================================================
# API pública unificada (motor único)
# ==========================================================
def calcular_strings_fv(
    *,
    n_paneles_total: int,
    panel: Any,
    inversor: Any,
    t_min_c: float,
    dos_aguas: bool = False,
    objetivo_dc_ac: float | None = None,
    pdc_kw_objetivo: float | None = None,
) -> Dict[str, Any]:
    """
    Motor único para strings (UI/NEC/PDF).
    Retorna dict estable:
      ok, errores, warnings, topologia, bounds, recomendacion, strings, meta
    """
    errores: List[str] = []
    warnings: List[str] = []

    n_total = _i(n_paneles_total, 0)
    if n_total <= 0:
        return {
            "ok": False,
            "errores": ["n_paneles_total inválido (<=0)."],
            "warnings": [],
            "topologia": "N/A",
            "bounds": {},
            "recomendacion": {},
            "strings": [],
            "meta": {},
        }

    try:
        tmin = float(t_min_c)
    except Exception:
        return {
            "ok": False,
            "errores": ["t_min_c inválido (no convertible a número)."],
            "warnings": [],
            "topologia": "N/A",
            "bounds": {},
            "recomendacion": {},
            "strings": [],
            "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas)},
        }

    # Acepta PanelSpec / InversorSpec directamente (motor puro)
    if not isinstance(panel, PanelSpec) or not isinstance(inversor, InversorSpec):
        return {
            "ok": False,
            "errores": ["calcular_strings_fv requiere PanelSpec e InversorSpec (normaliza en orquestador/entradas)."],
            "warnings": [],
            "topologia": "N/A",
            "bounds": {},
            "recomendacion": {},
            "strings": [],
            "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas), "t_min_c": tmin},
        }

    p: PanelSpec = panel
    inv: InversorSpec = inversor

    # Coherencia mínima
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
        return {
            "ok": False,
            "errores": errores,
            "warnings": warnings,
            "topologia": "N/A",
            "bounds": {},
            "recomendacion": {},
            "strings": [],
            "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas), "t_min_c": tmin},
        }

    rec = recomendar_string(
        panel=p,
        inversor=inv,
        t_min_c=tmin,
        objetivo_dc_ac=float(objetivo_dc_ac) if objetivo_dc_ac is not None else 1.2,
        pdc_kw_objetivo=float(pdc_kw_objetivo) if pdc_kw_objetivo is not None else None,
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
            "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas), "t_min_c": tmin},
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
            "meta": {"n_paneles_total": int(n_total), "dos_aguas": bool(dos_aguas), "t_min_c": tmin},
        }

    # Strings totales: por objetivo (ya viene)
    n_strings_total = _i(r.get("n_strings_total"), 0)
    if n_strings_total <= 0:
        # fallback por total paneles
        n_strings_total = max(1, int(ceil(n_total / max(n_series, 1))))

    # Topología
    topologia = "2-aguas" if (bool(dos_aguas) and inv.n_mppt >= 2) else "1-agua"
    ramas = _split_por_mppt(n_strings_total=n_strings_total, n_mppt=inv.n_mppt, dos_aguas=bool(dos_aguas))

    strings: List[Dict[str, Any]] = []
    for rama in ramas:
        mppt = int(rama["mppt"])
        n_paralelo = int(rama["n_strings"])
        etiqueta = str(rama.get("etiqueta") or "Arreglo FV")

        i_mppt_a = float(p.imp_a) * float(n_paralelo)
        ok_corr = i_mppt_a <= inv.imppt_max_a + 1e-9
        if not ok_corr:
            warnings.append(
                f"Corriente MPPT alta en MPPT {mppt}: {i_mppt_a:.2f} A > {inv.imppt_max_a:.2f} A."
            )

        strings.append(
            {
                "mppt": mppt,
                "etiqueta": etiqueta,
                "n_series": int(n_series),
                "n_paralelo": int(n_paralelo),
                "vmp_string_v": float(r.get("vmp_string_v") or 0.0),
                "voc_frio_string_v": float(r.get("voc_frio_string_v") or 0.0),
                "imp_a": float(p.imp_a),
                "isc_a": float(p.isc_a),
                "i_mppt_a": float(i_mppt_a),
            }
        )

    # Recomendación unificada
    recomendacion = {
        "n_series": int(n_series),
        "n_paneles_string": int(n_series),  # alias estable
        "n_strings_total": int(n_strings_total),
        "strings_por_mppt": int(ceil(n_strings_total / max(inv.n_mppt, 1))),
        "vmp_string_v": float(r.get("vmp_string_v") or 0.0),
        "voc_frio_string_v": float(r.get("voc_frio_string_v") or 0.0),
        "pdc_obj_kw": float(r.get("pdc_obj_kw") or 0.0),
        "p_string_kw_stc": float(r.get("p_string_kw_stc") or 0.0),
    }

    meta = {
        "n_paneles_total": int(n_total),
        "dos_aguas": bool(dos_aguas),
        "n_mppt": int(inv.n_mppt),
        "t_min_c": float(tmin),
    }

    return {
        "ok": True,
        "errores": [],
        "warnings": list(rec.get("warnings") or []) + warnings,
        "topologia": topologia,
        "bounds": rec.get("bounds") or {},
        "recomendacion": recomendacion,
        "strings": strings,
        "meta": meta,
    }


# Compatibilidad con nombre anterior
calcular_strings_auto = calcular_strings_fv
