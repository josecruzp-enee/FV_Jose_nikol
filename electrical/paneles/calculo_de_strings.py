# electrical/calculo_de_strings.py
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
    coef_voc_pct_c: float  # ej -0.25 (%/°C)


@dataclass(frozen=True)
class InversorSpec:
    pac_kw: float
    vdc_max_v: float
    mppt_min_v: float
    mppt_max_v: float
    n_mppt: int
    imppt_max_a: float


# ==========================================================
# Utilitarios numéricos
# ==========================================================
def _a_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _a_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return int(default)


# ==========================================================
# Cálculos base
# ==========================================================
def _voc_frio(*, voc_stc: float, coef_voc_pct_c: float, t_min_c: float, t_stc_c: float = 25.0) -> float:
    """
    Voc(T) = Voc_STC * (1 + coef%/°C/100 * (T - 25))
    """
    return float(voc_stc) * (1.0 + (float(coef_voc_pct_c) / 100.0) * (float(t_min_c) - float(t_stc_c)))


def _limites_por_voltaje(*, panel: PanelSpec, inv: InversorSpec, t_min_c: float) -> Dict[str, Any]:
    voc_frio_v = _voc_frio(voc_stc=panel.voc_v, coef_voc_pct_c=panel.coef_voc_pct_c, t_min_c=t_min_c)

    # Límite por Vdc max (con Voc frío)
    max_por_vdc = floor(inv.vdc_max_v / max(voc_frio_v, 1e-9))

    # Límite por MPPT (Vmp STC como aproximación)
    min_por_mppt = ceil(inv.mppt_min_v / max(panel.vmp_v, 1e-9))
    max_por_mppt = floor(inv.mppt_max_v / max(panel.vmp_v, 1e-9))

    n_max = max(0, min(max_por_vdc, max_por_mppt))
    n_min = max(1, min_por_mppt)

    return {
        "voc_frio_v": float(voc_frio_v),
        "n_min": int(n_min),
        "n_max": int(n_max),
        "max_por_vdc": int(max_por_vdc),
        "min_por_mppt": int(min_por_mppt),
        "max_por_mppt": int(max_por_mppt),
    }


def _limite_corriente_mppt(*, panel: PanelSpec, inv: InversorSpec, strings_por_mppt: int) -> Dict[str, Any]:
    i_mppt_a = panel.imp_a * int(strings_por_mppt)
    ok = i_mppt_a <= inv.imppt_max_a + 1e-9
    return {"i_mppt_a": float(i_mppt_a), "ok": bool(ok)}


def _score_n(*, n_series: int, panel: PanelSpec, inv: InversorSpec) -> float:
    """
    Score simple: acercar Vmp_string al centro de la ventana MPPT.
    Menor es mejor.
    """
    vmp_string = int(n_series) * panel.vmp_v
    mid = (inv.mppt_min_v + inv.mppt_max_v) / 2.0
    return abs(vmp_string - mid)


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
    Recomienda:
    - N paneles en serie por string (n_paneles_string)
    - strings totales (n_strings_total)
    - strings por MPPT (strings_por_mppt)

    Si pdc_kw_objetivo no se pasa, se usa: objetivo_dc_ac * pac_kw.
    """
    errores: List[str] = []
    warnings: List[str] = []

    if inversor.n_mppt <= 0:
        errores.append("Inversor inválido: n_mppt <= 0.")
    if panel.pmax_w <= 0 or panel.vmp_v <= 0 or panel.voc_v <= 0:
        errores.append("Panel inválido: revisar STC (pmax/vmp/voc).")

    if errores:
        return {"ok": False, "errores": errores, "warnings": warnings}

    bounds = _limites_por_voltaje(panel=panel, inv=inversor, t_min_c=float(t_min_c))
    n_min, n_max = int(bounds["n_min"]), int(bounds["n_max"])

    if n_max < n_min:
        errores.append(
            f"No existe N válido: n_min={n_min}, n_max={n_max}. "
            f"Revisa MPPT o Vdc_max vs Voc frío."
        )
        return {"ok": False, "errores": errores, "warnings": warnings, "bounds": bounds}

    # Elegir N recomendado por score
    candidatos = list(range(n_min, n_max + 1))
    n_rec = min(candidatos, key=lambda n: _score_n(n_series=n, panel=panel, inv=inversor))

    # Potencia DC objetivo
    pdc_obj_kw = float(pdc_kw_objetivo) if pdc_kw_objetivo is not None else (float(objetivo_dc_ac) * inversor.pac_kw)
    pdc_obj_w = pdc_obj_kw * 1000.0

    # Potencia de un string (STC)
    p_string_w = n_rec * panel.pmax_w

    # Strings totales requeridos
    n_strings_total = max(1, int(ceil(pdc_obj_w / max(p_string_w, 1e-9))))

    # Reparto por MPPT
    strings_por_mppt = max(1, int(ceil(n_strings_total / max(inversor.n_mppt, 1))))

    # Corriente MPPT (referencial)
    corr = _limite_corriente_mppt(panel=panel, inv=inversor, strings_por_mppt=strings_por_mppt)
    if not corr["ok"]:
        warnings.append(
            f"Corriente MPPT alta: {corr['i_mppt_a']:.2f} A > {inversor.imppt_max_a:.2f} A. "
            f"Reduce strings por MPPT o cambia inversor."
        )

    # Checks voltaje finales
    voc_frio_total = float(bounds["voc_frio_v"]) * n_rec
    if voc_frio_total > inversor.vdc_max_v + 1e-9:
        errores.append(f"Voc frío total excede Vdc_max: {voc_frio_total:.1f} V > {inversor.vdc_max_v:.1f} V")

    vmp_total = panel.vmp_v * n_rec
    if vmp_total < inversor.mppt_min_v - 1e-9 or vmp_total > inversor.mppt_max_v + 1e-9:
        warnings.append(
            f"Vmp string fuera de MPPT (referencial): {vmp_total:.1f} V vs "
            f"{inversor.mppt_min_v:.1f}-{inversor.mppt_max_v:.1f} V."
        )

    return {
        "ok": len(errores) == 0,
        "errores": errores,
        "warnings": warnings,
        "bounds": bounds,
        "recomendacion": {
            "n_paneles_string": int(n_rec),
            "n_strings_total": int(n_strings_total),
            "strings_por_mppt": int(strings_por_mppt),
            "pdc_obj_kw": float(pdc_obj_kw),
            "p_string_kw_stc": float(p_string_w / 1000.0),
            "vmp_string_v": float(vmp_total),
            "voc_frio_string_v": float(voc_frio_total),
            "i_mppt_a": float(corr["i_mppt_a"]),
        },
    }


# ==========================================================
# Normalización de entradas (catálogo → Spec)
# ==========================================================
def _panel_a_spec(panel: Any) -> PanelSpec:
    if isinstance(panel, PanelSpec):
        return panel

    coef = _a_float(getattr(panel, "coef_voc_pct_c", getattr(panel, "coef_voc", -0.28)), -0.28)
    return PanelSpec(
        pmax_w=_a_float(getattr(panel, "w", getattr(panel, "pmax_w", 0.0))),
        vmp_v=_a_float(getattr(panel, "vmp", getattr(panel, "vmp_v", 0.0))),
        voc_v=_a_float(getattr(panel, "voc", getattr(panel, "voc_v", 0.0))),
        imp_a=_a_float(getattr(panel, "imp", getattr(panel, "imp_a", 0.0))),
        isc_a=_a_float(getattr(panel, "isc", getattr(panel, "isc_a", 0.0))),
        coef_voc_pct_c=_a_float(coef),
    )


def _inversor_a_spec(inversor: Any) -> InversorSpec:
    if isinstance(inversor, InversorSpec):
        return inversor

    pac_kw = _a_float(getattr(inversor, "kw_ac", getattr(inversor, "pac_kw", 0.0)))
    imppt = getattr(inversor, "imppt_max_a", None)
    if imppt is None:
        imppt = getattr(inversor, "imppt_max", 25.0)

    return InversorSpec(
        pac_kw=_a_float(pac_kw),
        vdc_max_v=_a_float(getattr(inversor, "vdc_max", getattr(inversor, "vdc_max_v", 0.0))),
        mppt_min_v=_a_float(getattr(inversor, "vmppt_min", getattr(inversor, "mppt_min_v", 0.0))),
        mppt_max_v=_a_float(getattr(inversor, "vmppt_max", getattr(inversor, "mppt_max_v", 0.0))),
        n_mppt=_a_int(getattr(inversor, "n_mppt", 1), 1) or 1,
        imppt_max_a=_a_float(imppt, 25.0),
    )


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
    Retorna dict estable: ok/errores/warnings/recomendacion/strings/bounds/meta
    """
    n_total = _a_int(n_paneles_total, 0)
    if n_total <= 0:
        return {
            "ok": False,
            "errores": ["n_paneles_total inválido (<=0)."],
            "warnings": [],
            "recomendacion": {},
            "strings": [],
            "bounds": {},
            "meta": {},
        }

    p = _panel_a_spec(panel)
    inv = _inversor_a_spec(inversor)

    rec = recomendar_string(
        panel=p,
        inversor=inv,
        t_min_c=float(t_min_c),
        objetivo_dc_ac=float(objetivo_dc_ac) if objetivo_dc_ac is not None else 1.2,
        pdc_kw_objetivo=float(pdc_kw_objetivo) if pdc_kw_objetivo is not None else None,
    ) or {}

    if not rec.get("ok", False):
        return {
            "ok": False,
            "errores": list(rec.get("errores") or ["No se pudo recomendar string."]),
            "warnings": list(rec.get("warnings") or []),
            "recomendacion": rec.get("recomendacion") or {},
            "strings": [],
            "bounds": rec.get("bounds") or {},
            "meta": {},
        }

    r = rec.get("recomendacion") or {}
    n_series = _a_int(r.get("n_paneles_string"), 0)
    if n_series <= 0:
        return {
            "ok": False,
            "errores": ["recomendar_string no retornó n_paneles_string válido."],
            "warnings": list(rec.get("warnings") or []),
            "recomendacion": r,
            "strings": [],
            "bounds": rec.get("bounds") or {},
            "meta": {},
        }

    # Derivar strings por total paneles (si aplica)
    n_strings_total = _a_int(r.get("n_strings_total"), 0)
    if n_strings_total <= 0:
        n_strings_total = max(1, int((n_total + n_series - 1) // n_series))

    strings_por_mppt = _a_int(r.get("strings_por_mppt"), 0)
    if strings_por_mppt <= 0:
        strings_por_mppt = max(1, int(ceil(n_strings_total / max(inv.n_mppt, 1))))

    # Topología por MPPT
    topologia = "2-aguas" if (bool(dos_aguas) and inv.n_mppt >= 2) else "1-agua"

    strings: list[dict] = []
    if topologia == "2-aguas":
        s1 = n_strings_total // 2
        s2 = n_strings_total - s1
        partes = [(1, s1, "Techo izquierdo"), (2, s2, "Techo derecho")]
    else:
        partes = [(1, n_strings_total, "Arreglo FV")]

    for mppt, n_paralelo, etiqueta in partes:
        if n_paralelo <= 0:
            continue
        strings.append(
            {
                "mppt": int(mppt),
                "etiqueta": str(etiqueta),
                "n_series": int(n_series),
                "n_paralelo": int(n_paralelo),
                "vmp_string_v": _a_float(r.get("vmp_string_v"), 0.0),
                "voc_frio_string_v": _a_float(r.get("voc_frio_string_v"), 0.0),
                "imp_a": float(p.imp_a),
                "isc_a": float(p.isc_a),
            }
        )

    recomendacion = {
        "n_paneles_string": int(n_series),
        "n_strings_total": int(n_strings_total),
        "strings_por_mppt": int(strings_por_mppt),
        "vmp_string_v": _a_float(r.get("vmp_string_v"), 0.0),
        "voc_frio_string_v": _a_float(r.get("voc_frio_string_v"), 0.0),
        "i_mppt_a": _a_float(r.get("i_mppt_a"), 0.0),
        "pdc_obj_kw": _a_float(r.get("pdc_obj_kw"), 0.0),
        "p_string_kw_stc": _a_float(r.get("p_string_kw_stc"), 0.0),
    }

    meta = {
        "n_paneles_total": int(n_total),
        "dos_aguas": bool(dos_aguas),
        "n_mppt": int(inv.n_mppt),
        "t_min_c": float(t_min_c),
    }
    pid = getattr(panel, "id", None)
    iid = getattr(inversor, "id", None)
    if pid is not None:
        meta["panel_id"] = str(pid)
    if iid is not None:
        meta["inversor_id"] = str(iid)

    return {
        "ok": True,
        "warnings": list(rec.get("warnings") or []),
        "errores": [],
        "topologia": topologia,
        "bounds": rec.get("bounds") or {},
        "recomendacion": recomendacion,
        "strings": strings,
        "meta": meta,
    }


# Compatibilidad con nombre anterior (si UI u otros módulos aún lo usan)
calcular_strings_auto = calcular_strings_fv
