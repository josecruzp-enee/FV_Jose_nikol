# electrical/paneles/orquestador_paneles.py
# Orquestador del dominio paneles: normaliza entradas, valida coherencia mínima y ejecuta el motor único de strings FV.
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .calculo_de_strings import InversorSpec, PanelSpec, calcular_strings_fv
from .dimensionado_paneles import calcular_panel_sizing
from .resumen_strings import resumen_strings
from .validacion_strings import (
    validar_inversor,
    validar_panel,
    validar_parametros_generales,
)


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


# Normaliza panel (legacy/nuevo/UI) al contrato interno PanelSpec.
def _as_panel_spec(panel: Any) -> PanelSpec:
    if isinstance(panel, PanelSpec):
        return panel

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


# Normaliza inversor (legacy/nuevo/UI) al contrato interno InversorSpec.
def _as_inversor_spec(inversor: Any) -> InversorSpec:
    if isinstance(inversor, InversorSpec):
        return inversor

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


# Ejecuta el cálculo completo de strings: normaliza, valida, llama al motor y unifica salida.
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

    n_total = _i(n_paneles_total, 0) if n_paneles_total is not None else 0
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

    # Temperatura operativa (conservador por defecto).
    t_oper = float(t_oper_c) if t_oper_c is not None else 55.0

    # Normalización a contrato interno estable.
    p = _as_panel_spec(panel)
    inv = _as_inversor_spec(inversor)

    # Validación dominio (pura, sin cálculos de strings).
    e, w = validar_panel(p)
    errores += e
    warnings += w

    e, w = validar_inversor(inv)
    errores += e
    warnings += w

    e, w = validar_parametros_generales(n_total, tmin)
    errores += e
    warnings += w

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
                "t_oper_c": t_oper,
                "panel_spec": p.__dict__ if hasattr(p, "__dict__") else {},
                "inversor_spec": inv.__dict__ if hasattr(inv, "__dict__") else {},
            },
        }

    # Motor FV (único).
    out = calcular_strings_fv(
        n_paneles_total=n_total,
        panel=p,
        inversor=inv,
        t_min_c=tmin,
        dos_aguas=bool(dos_aguas),
        objetivo_dc_ac=float(objetivo_dc_ac) if objetivo_dc_ac is not None else None,
        pdc_kw_objetivo=float(pdc_kw_objetivo) if pdc_kw_objetivo is not None else None,
        t_oper_c=t_oper,
    ) or {}

    # Normaliza contrato de salida.
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
    meta.setdefault("t_oper_c", t_oper)
    meta.setdefault("panel_spec", p.__dict__ if hasattr(p, "__dict__") else {})
    meta.setdefault("inversor_spec", inv.__dict__ if hasattr(inv, "__dict__") else {})
    out["meta"] = meta

    # Agrega warnings locales del orquestador.
    out["warnings"] = list(out.get("warnings") or []) + warnings

    return out


# Orquestador único del dominio (modo demanda): consumo + cobertura => sizing => strings => resumen.
def ejecutar_paneles_por_demanda(
    *,
    consumo_12m_kwh: float,
    cobertura_pct: float,
    panel: Any,
    inversor: Any,
    t_min_c: float,
    dos_aguas: bool = False,
    objetivo_dc_ac: float | None = None,
    t_oper_c: float | None = None,
) -> Dict[str, Any]:
    """
    Entrada mínima UI:
      - consumo_12m_kwh, cobertura_pct, panel(catálogo), inversor(catálogo), t_min_c, dos_aguas (opcional)

    Devuelve paquete unificado:
      - sizing (n_paneles, pdc_kw, etc)
      - strings (raw)
      - resumen (shape estable UI/PDF)
    """
    # 1) Dimensionado por energía
    sizing = calcular_panel_sizing(
        consumo_12m_kwh=float(consumo_12m_kwh),
        cobertura_pct=float(cobertura_pct),
        panel=panel,
    )

    # Soporta dataclass o dict (sin adivinar demasiado)
    if isinstance(sizing, dict):
        ok_sizing = bool(sizing.get("ok", True))
        n_paneles = _i(sizing.get("n_paneles", 0), 0)
        pdc_kw = _f(sizing.get("pdc_kw", 0.0), 0.0)
        err_sizing = list(sizing.get("errores") or [])
        warn_sizing = list(sizing.get("warnings") or [])
    else:
        ok_sizing = bool(getattr(sizing, "ok", True))
        n_paneles = _i(getattr(sizing, "n_paneles", 0), 0)
        pdc_kw = _f(getattr(sizing, "pdc_kw", 0.0), 0.0)
        err_sizing = list(getattr(sizing, "errores", []) or [])
        warn_sizing = list(getattr(sizing, "warnings", []) or [])

    if (not ok_sizing) or n_paneles <= 0 or pdc_kw <= 0:
        return {
            "ok": False,
            "errores": err_sizing or ["Dimensionado inválido (n_paneles/pdc_kw)."],
            "warnings": warn_sizing,
            "sizing": sizing,
            "strings": {},
            "resumen": {},
        }

    # 2) Strings (ingeniería DC) usando el motor único
    strings_out = ejecutar_calculo_strings(
        n_paneles_total=int(n_paneles),
        panel=panel,
        inversor=inversor,
        t_min_c=float(t_min_c),
        dos_aguas=bool(dos_aguas),
        objetivo_dc_ac=float(objetivo_dc_ac) if objetivo_dc_ac is not None else None,
        pdc_kw_objetivo=float(pdc_kw),
        t_oper_c=float(t_oper_c) if t_oper_c is not None else None,
    )

    # 3) Resumen estable (UI/PDF)
    resumen = resumen_strings(strings_out)

    return {
        "ok": bool(strings_out.get("ok")),
        "errores": err_sizing + list(strings_out.get("errores") or []),
        "warnings": warn_sizing + list(strings_out.get("warnings") or []),
        "sizing": sizing,
        "strings": strings_out,
        "resumen": resumen,
    }


# Convierte resultado a líneas legibles (UI/PDF).
def a_lineas_strings(cfg: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    cfg = dict(cfg or {})
    rec = (cfg.get("recomendacion") or {}) if isinstance(cfg.get("recomendacion"), dict) else {}
    p_string_kw = _f(rec.get("p_string_kw_stc", 0.0), 0.0)

    for s in (cfg.get("strings") or []):
        etiqueta = str(s.get("etiqueta") or "Arreglo FV")
        ns = _i(s.get("n_series", s.get("ns", 0)), 0)
        np_ = _i(s.get("n_paralelo", s.get("np", 1)), 1) or 1

        vmp = _f(s.get("vmp_string_v", s.get("vmp_V", 0.0)), 0.0)  # Vmp caliente
        voc_frio = _f(s.get("voc_frio_string_v", s.get("voc_frio_V", 0.0)), 0.0)
        imp = _f(s.get("imp_a", s.get("imp_A", 0.0)), 0.0)

        pdc_kw = p_string_kw * float(np_) if p_string_kw > 0 else 0.0

        if pdc_kw > 0:
            lines.append(
                f"{etiqueta} — {ns}S×{np_}P ({np_} string): "
                f"Vmp_hot≈{vmp:.0f} V | Voc_frío≈{voc_frio:.0f} V | Imp≈{imp:.1f} A | "
                f"Pdc≈{pdc_kw:.2f} kW."
            )
        else:
            lines.append(
                f"{etiqueta} — {ns}S×{np_}P ({np_} string): "
                f"Vmp_hot≈{vmp:.0f} V | Voc_frío≈{voc_frio:.0f} V | Imp≈{imp:.1f} A."
            )

    return lines


# Alias simple: ejecuta strings DC desde inputs simples (compatibilidad).
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
