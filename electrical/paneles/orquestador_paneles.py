from __future__ import annotations

from typing import Any, Dict, List

from .calculo_de_strings import PanelSpec, InversorSpec, calcular_strings_fv


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
    """
    Normaliza panel -> PanelSpec.

    Soporta:
      - PanelSpec directo
      - legacy con atributos: w/vmp/voc/imp/isc
      - UI legacy: voc_stc/vmp_stc/isc/imp/pmax_w
      - nuevo: pmax_w/vmp_v/voc_v/imp_a/isc_a
      - coef: coef_voc_pct_c | coef_voc | tc_voc_pct_c (default -0.28 %/°C)
    """
    if isinstance(panel, PanelSpec):
        return panel

    coef = _f(
        getattr(
            panel,
            "coef_voc_pct_c",
            getattr(panel, "coef_voc", getattr(panel, "tc_voc_pct_c", -0.28)),
        ),
        -0.28,
    )

    # Voc/Vmp soporta variantes
    voc = getattr(panel, "voc", getattr(panel, "voc_v", getattr(panel, "voc_stc", 0.0)))
    vmp = getattr(panel, "vmp", getattr(panel, "vmp_v", getattr(panel, "vmp_stc", 0.0)))
    isc = getattr(panel, "isc", getattr(panel, "isc_a", 0.0))
    imp = getattr(panel, "imp", getattr(panel, "imp_a", 0.0))
    pmax = getattr(panel, "w", getattr(panel, "pmax_w", getattr(panel, "pmax", 0.0)))

    return PanelSpec(
        pmax_w=_f(pmax, 0.0),
        vmp_v=_f(vmp, 0.0),
        voc_v=_f(voc, 0.0),
        imp_a=_f(imp, 0.0),
        isc_a=_f(isc, 0.0),
        coef_voc_pct_c=_f(coef, -0.28),
    )


def _as_inversor_spec(inversor: Any) -> InversorSpec:
    """
    Normaliza inversor -> InversorSpec.

    Soporta:
      - InversorSpec directo
      - legacy: kw_ac, vdc_max, vmppt_min, vmppt_max, n_mppt, imppt_max|imppt_max_a
      - UI legacy: vdc_max, mppt_min, mppt_max, imppt_max, n_mppt, pac_kw
      - nuevo: pac_kw, vdc_max_v, mppt_min_v, mppt_max_v, n_mppt, imppt_max_a
    """
    if isinstance(inversor, InversorSpec):
        return inversor

    imppt = getattr(inversor, "imppt_max_a", None)
    if imppt is None:
        imppt = getattr(inversor, "imppt_max", 25.0)

    n_mppt = _i(getattr(inversor, "n_mppt", 1), 1) or 1

    return InversorSpec(
        pac_kw=_f(getattr(inversor, "kw_ac", getattr(inversor, "pac_kw", 0.0))),
        vdc_max_v=_f(getattr(inversor, "vdc_max", getattr(inversor, "vdc_max_v", 0.0))),
        mppt_min_v=_f(getattr(inversor, "vmppt_min", getattr(inversor, "mppt_min_v", getattr(inversor, "mppt_min", 0.0)))),
        mppt_max_v=_f(getattr(inversor, "vmppt_max", getattr(inversor, "mppt_max_v", getattr(inversor, "mppt_max", 0.0)))),
        n_mppt=n_mppt,
        imppt_max_a=_f(imppt, 25.0),
    )


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
    Orquesta el cálculo de strings (UI/NEC/PDF).
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
            "meta": {"n_paneles_total": n_total, "dos_aguas": bool(dos_aguas)},
        }

    try:
        tmin = float(t_min_c)
    except Exception:
        return {
            "ok": False,
            "errores": ["t_min_c inválido (no convertible a número)."],
            "warnings": [],
            "topologia": "N/A",
            "strings": [],
            "recomendacion": {},
            "bounds": {},
            "meta": {"n_paneles_total": n_total, "dos_aguas": bool(dos_aguas)},
        }

    # Normalización
    p = _as_panel_spec(panel)
    inv = _as_inversor_spec(inversor)

    # Validación mínima
    if p.pmax_w <= 0 or p.vmp_v <= 0 or p.voc_v <= 0:
        errores.append("Panel inválido: revisar pmax/vmp/voc (>0).")

    if inv.vdc_max_v <= 0 or inv.mppt_min_v <= 0 or inv.mppt_max_v <= 0 or inv.n_mppt <= 0:
        errores.append("Inversor inválido: revisar vdc_max/mppt/n_mppt (>0).")

    if inv.imppt_max_a <= 0:
        errores.append("Inversor inválido: imppt_max_a debe ser > 0.")

    if inv.mppt_min_v >= inv.mppt_max_v:
        errores.append("Inversor inválido: mppt_min_v debe ser < mppt_max_v.")

    if inv.vdc_max_v > 0 and inv.mppt_max_v > 0 and inv.vdc_max_v < inv.mppt_max_v:
        warnings.append("Aviso: vdc_max_v < mppt_max_v (revisar datasheet).")

    if p.coef_voc_pct_c >= 0:
        warnings.append("Aviso: coef_voc_pct_c >= 0 (típicamente es negativo).")

    if errores:
        return {
            "ok": False,
            "errores": errores,
            "warnings": warnings,
            "topologia": "N/A",
            "strings": [],
            "recomendacion": {},
            "bounds": {},
            "meta": {
                "n_paneles_total": n_total,
                "dos_aguas": bool(dos_aguas),
                "t_min_c": tmin,
                "panel_spec": p.__dict__,
                "inversor_spec": inv.__dict__,
            },
        }

    out = calcular_strings_fv(
        n_paneles_total=n_total,
        panel=p,
        inversor=inv,
        t_min_c=tmin,
        dos_aguas=bool(dos_aguas),
        objetivo_dc_ac=float(objetivo_dc_ac) if objetivo_dc_ac is not None else None,
        pdc_kw_objetivo=float(pdc_kw_objetivo) if pdc_kw_objetivo is not None else None,
    )

    out.setdefault("ok", False)
    out.setdefault("errores", [])
    out.setdefault("warnings", [])
    out.setdefault("topologia", "N/A")
    out.setdefault("strings", [])
    out.setdefault("recomendacion", {})
    out.setdefault("bounds", {})
    out.setdefault("meta", {})

    meta = out["meta"] if isinstance(out.get("meta"), dict) else {}
    meta.setdefault("n_paneles_total", n_total)
    meta.setdefault("dos_aguas", bool(dos_aguas))
    meta.setdefault("t_min_c", tmin)
    meta.setdefault("panel_spec", p.__dict__)
    meta.setdefault("inversor_spec", inv.__dict__)
    out["meta"] = meta

    return out


def a_lineas_strings(cfg: Dict[str, Any]) -> List[str]:
    """
    Líneas listas para UI/PDF.
    """
    lines: List[str] = []
    rec = (cfg.get("recomendacion") or {}) if isinstance(cfg, dict) else {}

    p_string_kw = _f(rec.get("p_string_kw_stc", 0.0), 0.0)

    for s in (cfg.get("strings") or []):
        etiqueta = s.get("etiqueta", "Arreglo FV")

        ns = int(s.get("n_series", s.get("ns", 0)) or 0)
        np_ = int(s.get("n_paralelo", s.get("np", 1)) or 1)
        nstr = np_

        vmp = _f(s.get("vmp_string_v", s.get("vmp_V", 0.0)), 0.0)
        voc_frio = _f(s.get("voc_frio_string_v", s.get("voc_frio_V", 0.0)), 0.0)
        imp = _f(s.get("imp_a", s.get("imp_A", 0.0)), 0.0)

        pdc_kw = p_string_kw * nstr if p_string_kw > 0 else 0.0

        if pdc_kw > 0:
            lines.append(
                f"{etiqueta} — {ns}S×{np_}P ({nstr} string): "
                f"Vmp≈{vmp:.0f} V | Voc frío≈{voc_frio:.0f} V | Imp≈{imp:.1f} A | "
                f"Pdc≈{pdc_kw:.2f} kW."
            )
        else:
            lines.append(
                f"{etiqueta} — {ns}S×{np_}P ({nstr} string): "
                f"Vmp≈{vmp:.0f} V | Voc frío≈{voc_frio:.0f} V | Imp≈{imp:.1f} A."
            )

    return lines


def calcular_strings_dc(
    *,
    n_paneles: int,
    panel: Any,
    inversor: Any,
    dos_aguas: bool,
    t_min_c: float = 10.0,
    t_ref_c: float = 25.0,  # compat (no usado)
    min_modulos_serie: int = 6,  # compat (no usado)
) -> Dict[str, Any]:
    return ejecutar_calculo_strings(
        n_paneles_total=int(n_paneles),
        panel=panel,
        inversor=inversor,
        dos_aguas=bool(dos_aguas),
        t_min_c=float(t_min_c),
    )


def a_lineas(cfg: Dict[str, Any]) -> List[str]:
    return a_lineas_strings(cfg)
