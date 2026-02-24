# electrical/paneles/orquestador_paneles.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .calculo_de_strings import PanelSpec, InversorSpec, calcular_strings_fv


# -----------------------
# Utilitarios cortos
# -----------------------
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


def _as_panel_spec(panel: Any) -> PanelSpec:
    if isinstance(panel, PanelSpec):
        return panel
    coef = _f(getattr(panel, "coef_voc_pct_c", getattr(panel, "coef_voc", getattr(panel, "tc_voc_pct_c", -0.28))), -0.28)
    # compat con tu modelo viejo: panel.w/vmp/voc/imp/isc
    return PanelSpec(
        pmax_w=_f(getattr(panel, "w", getattr(panel, "pmax_w", 0.0))),
        vmp_v=_f(getattr(panel, "vmp", getattr(panel, "vmp_v", 0.0))),
        voc_v=_f(getattr(panel, "voc", getattr(panel, "voc_v", 0.0))),
        imp_a=_f(getattr(panel, "imp", getattr(panel, "imp_a", 0.0))),
        isc_a=_f(getattr(panel, "isc", getattr(panel, "isc_a", 0.0))),
        coef_voc_pct_c=_f(coef, -0.28),
    )


def _as_inversor_spec(inversor: Any) -> InversorSpec:
    if isinstance(inversor, InversorSpec):
        return inversor

    imppt = getattr(inversor, "imppt_max_a", None)
    if imppt is None:
        imppt = getattr(inversor, "imppt_max", 25.0)

    return InversorSpec(
        pac_kw=_f(getattr(inversor, "kw_ac", getattr(inversor, "pac_kw", 0.0))),
        vdc_max_v=_f(getattr(inversor, "vdc_max", getattr(inversor, "vdc_max_v", 0.0))),
        mppt_min_v=_f(getattr(inversor, "vmppt_min", getattr(inversor, "mppt_min_v", 0.0))),
        mppt_max_v=_f(getattr(inversor, "vmppt_max", getattr(inversor, "mppt_max_v", 0.0))),
        n_mppt=_i(getattr(inversor, "n_mppt", 1), 1) or 1,
        imppt_max_a=_f(imppt, 25.0),
    )


# -----------------------
# API pública (orquestador)
# -----------------------
def ejecutar_calculo_strings(
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
    Orquesta el cálculo de strings para Paso 5 (UI/NEC/PDF).
    Entrada → Validación básica → Cálculo (motor) → Salida estable.

    Retorna dict estable:
      ok, errores, warnings, topologia, strings, recomendacion, bounds, meta
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
            "strings": [],
            "recomendacion": {},
            "bounds": {},
            "meta": {},
        }

    p = _as_panel_spec(panel)
    inv = _as_inversor_spec(inversor)

    # Validación mínima (sin meternos a NEC todavía)
    if p.pmax_w <= 0 or p.vmp_v <= 0 or p.voc_v <= 0:
        errores.append("Panel inválido: revisar pmax/vmp/voc.")
    if inv.vdc_max_v <= 0 or inv.mppt_min_v <= 0 or inv.mppt_max_v <= 0 or inv.n_mppt <= 0:
        errores.append("Inversor inválido: revisar vdc_max/mppt/n_mppt.")
    if errores:
        return {
            "ok": False,
            "errores": errores,
            "warnings": warnings,
            "topologia": "N/A",
            "strings": [],
            "recomendacion": {},
            "bounds": {},
            "meta": {"n_paneles_total": n_total, "dos_aguas": bool(dos_aguas), "t_min_c": float(t_min_c)},
        }

    out = calcular_strings_fv(
        n_paneles_total=n_total,
        panel=p,
        inversor=inv,
        t_min_c=float(t_min_c),
        dos_aguas=bool(dos_aguas),
        objetivo_dc_ac=float(objetivo_dc_ac) if objetivo_dc_ac is not None else None,
        pdc_kw_objetivo=float(pdc_kw_objetivo) if pdc_kw_objetivo is not None else None,
    )

    # out ya es estable. Solo garantizamos claves mínimas.
    out.setdefault("ok", False)
    out.setdefault("errores", [])
    out.setdefault("warnings", [])
    out.setdefault("topologia", "N/A")
    out.setdefault("strings", [])
    out.setdefault("recomendacion", {})
    out.setdefault("bounds", {})
    out.setdefault("meta", {})
    return out


def a_lineas_strings(cfg: Dict[str, Any]) -> List[str]:
    """Líneas listas para UI/PDF (compat con tu función anterior a_lineas)."""
    lines: List[str] = []
    for s in (cfg.get("strings") or []):
        # soportar claves nuevas del motor
        etiqueta = s.get("etiqueta", "Arreglo FV")
        ns = int(s.get("n_series", s.get("ns", 0)) or 0)
        vmp = _f(s.get("vmp_string_v", s.get("vmp_V", 0.0)), 0.0)
        voc_frio = _f(s.get("voc_frio_string_v", s.get("voc_frio_V", 0.0)), 0.0)
        imp = _f(s.get("imp_a", s.get("imp_A", 0.0)), 0.0)

        lines.append(
            f"{etiqueta} — {ns}S: Vmp≈{vmp:.0f} V | Voc frío≈{voc_frio:.0f} V | Imp≈{imp:.1f} A."
        )
    return lines
