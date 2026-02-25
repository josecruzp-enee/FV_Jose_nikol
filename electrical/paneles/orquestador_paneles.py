# Orquestador del dominio paneles: normaliza entradas, valida coherencia mínima y ejecuta el motor de strings FV.
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .calculo_de_strings import InversorSpec, PanelSpec, calcular_strings_fv
from .validacion_strings import InversorFV, PanelFV, validar_inversor, validar_panel, validar_parametros_generales


# Convierte cualquier valor a float seguro usando un valor por defecto.
def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


# Convierte cualquier valor a entero seguro usando un valor por defecto.
def _i(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return int(default)


# Normaliza objetos de panel (legacy/nuevo/UI) al contrato interno PanelSpec.
def _as_panel_spec(panel: Any) -> PanelSpec:
    if isinstance(panel, PanelSpec):
        return panel

    # Soporta PanelFV (validación/UI)
    if isinstance(panel, PanelFV):
        return PanelSpec(
            pmax_w=_f(getattr(panel, "pmax_w", 0.0), 0.0),
            vmp_v=_f(getattr(panel, "vmp_stc", 0.0), 0.0),
            voc_v=_f(getattr(panel, "voc_stc", 0.0), 0.0),
            imp_a=_f(getattr(panel, "imp", 0.0), 0.0),
            isc_a=_f(getattr(panel, "isc", 0.0), 0.0),
            coef_voc_pct_c=_f(getattr(panel, "coef_voc_pct_c", -0.28), -0.28),
            coef_vmp_pct_c=_f(getattr(panel, "coef_vmp_pct_c", -0.34), -0.34),
        )

    coef_voc = _f(
        getattr(panel, "coef_voc_pct_c", getattr(panel, "coef_voc", getattr(panel, "tc_voc_pct_c", -0.28))),
        -0.28,
    )

    coef_vmp = getattr(panel, "coef_vmp_pct_c", None)
    if coef_vmp is None:
        coef_vmp = getattr(panel, "coef_vmp", None)
    if coef_vmp is None:
        coef_vmp = getattr(panel, "tc_vmp_pct_c", None)
    if coef_vmp is None:
        coef_vmp = getattr(panel, "coef_pmax_pct_c", -0.34)

    return PanelSpec(
        pmax_w=_f(getattr(panel, "w", getattr(panel, "pmax_w", 0.0))),
        vmp_v=_f(getattr(panel, "vmp", getattr(panel, "vmp_v", 0.0))),
        voc_v=_f(getattr(panel, "voc", getattr(panel, "voc_v", 0.0))),
        imp_a=_f(getattr(panel, "imp", getattr(panel, "imp_a", 0.0))),
        isc_a=_f(getattr(panel, "isc", getattr(panel, "isc_a", 0.0))),
        coef_voc_pct_c=_f(coef_voc, -0.28),
        coef_vmp_pct_c=_f(coef_vmp, -0.34),
    )


# Normaliza objetos de inversor (legacy/nuevo/UI) al contrato interno InversorSpec.
def _as_inversor_spec(inversor: Any) -> InversorSpec:
    if isinstance(inversor, InversorSpec):
        return inversor

    # Soporta InversorFV (validación/UI)
    if isinstance(inversor, InversorFV):
        return InversorSpec(
            pac_kw=_f(getattr(inversor, "pac_kw", 0.0), 0.0),
            vdc_max_v=_f(getattr(inversor, "vdc_max", 0.0), 0.0),
            mppt_min_v=_f(getattr(inversor, "mppt_min", 0.0), 0.0),
            mppt_max_v=_f(getattr(inversor, "mppt_max", 0.0), 0.0),
            n_mppt=_i(getattr(inversor, "n_mppt", 1), 1) or 1,
            imppt_max_a=_f(getattr(inversor, "imppt_max", 0.0), 0.0),
        )

    # --- imppt_max_a: OBLIGATORIO para cálculo "a norma" ---
    imppt = getattr(inversor, "imppt_max_a", None)
    if imppt is None:
        imppt = getattr(inversor, "imppt_max", None)

    imppt_f = _f(imppt, 0.0) if imppt is not None else 0.0
    n_mppt = _i(getattr(inversor, "n_mppt", 1), 1) or 1

    return InversorSpec(
        pac_kw=_f(getattr(inversor, "kw_ac", getattr(inversor, "pac_kw", 0.0))),
        vdc_max_v=_f(getattr(inversor, "vdc_max", getattr(inversor, "vdc_max_v", 0.0))),
        mppt_min_v=_f(getattr(inversor, "vmppt_min", getattr(inversor, "mppt_min_v", 0.0))),
        mppt_max_v=_f(getattr(inversor, "vmppt_max", getattr(inversor, "mppt_max_v", 0.0))),
        n_mppt=n_mppt,
        imppt_max_a=imppt_f,
    )


# Ejecuta el cálculo completo de strings: normaliza, valida y llama al motor único.
def ejecutar_calculo_strings(
    *,
    n_paneles_total: Optional[int],
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

    # Nota: para strings "a norma" mantenemos n_paneles_total requerido (derivado del sizing).
    n_total = _i(n_paneles_total, 0) if n_paneles_total is not None else 0
    if n_total <= 0:
        return {
            "ok": False,
            "errores": ["n_paneles_total inválido (<=0). Debe venir derivado del dimensionado energético."],
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

    # Validación básica (sin cálculos) a través de los validadores puros.
    # Si panel/inversor no son PanelFV/InversorFV, creamos “vista” mínima para validar.
    panel_v = panel if isinstance(panel, PanelFV) else PanelFV(
        voc_stc=_f(getattr(panel, "voc_stc", getattr(panel, "voc", getattr(panel, "voc_v", 0.0))), 0.0),
        vmp_stc=_f(getattr(panel, "vmp_stc", getattr(panel, "vmp", getattr(panel, "vmp_v", 0.0))), 0.0),
        isc=_f(getattr(panel, "isc", getattr(panel, "isc_a", 0.0)), 0.0),
        imp=_f(getattr(panel, "imp", getattr(panel, "imp_a", 0.0)), 0.0),
        coef_voc_pct_c=_f(getattr(panel, "coef_voc_pct_c", getattr(panel, "coef_voc", getattr(panel, "tc_voc_pct_c", -0.28))), -0.28),
        pmax_w=_f(getattr(panel, "pmax_w", getattr(panel, "w", 0.0)), 0.0),
    )

    inversor_v = inversor if isinstance(inversor, InversorFV) else InversorFV(
        vdc_max=_f(getattr(inversor, "vdc_max", getattr(inversor, "vdc_max_v", 0.0)), 0.0),
        mppt_min=_f(getattr(inversor, "mppt_min", getattr(inversor, "vmppt_min", getattr(inversor, "mppt_min_v", 0.0))), 0.0),
        mppt_max=_f(getattr(inversor, "mppt_max", getattr(inversor, "vmppt_max", getattr(inversor, "mppt_max_v", 0.0))), 0.0),
        imppt_max=_f(getattr(inversor, "imppt_max", getattr(inversor, "imppt_max_a", 0.0)), 0.0),
        n_mppt=_i(getattr(inversor, "n_mppt", 1), 1) or 1,
        pac_kw=_f(getattr(inversor, "pac_kw", getattr(inversor, "kw_ac", 0.0)), 0.0),
    )

    e, w = validar_panel(panel_v)
    errores += e
    warnings += w

    e, w = validar_inversor(inversor_v)
    errores += e
    warnings += w

    e, w = validar_parametros_generales(n_total, tmin)
    errores += e
    warnings += w

    # Normalización a contrato interno estable.
    p = _as_panel_spec(panel)
    inv = _as_inversor_spec(inversor)

    # Warnings complementarios por coeficientes (sin duplicar errores).
    if p.coef_voc_pct_c >= 0:
        warnings.append("Aviso: coef_voc_pct_c >= 0 (típicamente es negativo).")
    if p.coef_vmp_pct_c >= 0:
        warnings.append("Aviso: coef_vmp_pct_c >= 0 (típicamente es negativo).")

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
                "panel_spec": p.__dict__ if hasattr(p, "__dict__") else {},
                "inversor_spec": inv.__dict__ if hasattr(inv, "__dict__") else {},
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
        # Nota: t_oper_c aún no está plumbed al motor en tu firma; queda guardado en meta para el siguiente paso.
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
    if t_oper_c is not None:
        meta.setdefault("t_oper_c", float(t_oper_c))
    meta.setdefault("panel_spec", p.__dict__ if hasattr(p, "__dict__") else {})
    meta.setdefault("inversor_spec", inv.__dict__ if hasattr(inv, "__dict__") else {})
    out["meta"] = meta

    # Agrega warnings del orquestador.
    out["warnings"] = list(out.get("warnings") or []) + warnings

    return out


# Convierte el resultado de strings a líneas legibles para UI/PDF.
def a_lineas_strings(cfg: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    rec = (cfg.get("recomendacion") or {}) if isinstance(cfg, dict) else {}
    p_string_kw = _f(rec.get("p_string_kw_stc", 0.0), 0.0)

    for s in (cfg.get("strings") or []):
        etiqueta = s.get("etiqueta", "Arreglo FV")
        ns = int(s.get("n_series", s.get("ns", 0)) or 0)
        np_ = int(s.get("n_paralelo", s.get("np", 1)) or 1)
        nstr = np_

        vmp = _f(s.get("vmp_string_v", s.get("vmp_V", 0.0)), 0.0)  # Vmp caliente
        voc_frio = _f(s.get("voc_frio_string_v", s.get("voc_frio_V", 0.0)), 0.0)
        imp = _f(s.get("imp_a", s.get("imp_A", 0.0)), 0.0)

        pdc_kw = p_string_kw * nstr if p_string_kw > 0 else 0.0

        if pdc_kw > 0:
            lines.append(
                f"{etiqueta} — {ns}S×{np_}P ({nstr} string): "
                f"Vmp_hot≈{vmp:.0f} V | Voc_frío≈{voc_frio:.0f} V | Imp≈{imp:.1f} A | "
                f"Pdc≈{pdc_kw:.2f} kW."
            )
        else:
            lines.append(
                f"{etiqueta} — {ns}S×{np_}P ({nstr} string): "
                f"Vmp_hot≈{vmp:.0f} V | Voc_frío≈{voc_frio:.0f} V | Imp≈{imp:.1f} A."
            )

    return lines


# Alias de compatibilidad: ejecuta strings DC desde inputs simples.
def calcular_strings_dc(
    *,
    n_paneles: int,
    panel: Any,
    inversor: Any,
    dos_aguas: bool,
    t_min_c: float = 10.0,
) -> Dict[str, Any]:
    return ejecutar_calculo_strings(
        n_paneles_total=int(n_paneles),
        panel=panel,
        inversor=inversor,
        dos_aguas=bool(dos_aguas),
        t_min_c=float(t_min_c),
    )


# Alias de compatibilidad para líneas de salida.
def a_lineas(cfg: Dict[str, Any]) -> List[str]:
    return a_lineas_strings(cfg)
