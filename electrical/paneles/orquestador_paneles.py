# electrical/paneles/orquestador_paneles.py
# Orquestador del dominio paneles: normaliza entradas, valida coherencia mínima
# y ejecuta el motor único de strings FV.

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


# ================================
# Helpers internos
# ================================

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


# ================================
# Normalización a contratos internos
# ================================

def _as_panel_spec(panel: Any) -> PanelSpec:
    if isinstance(panel, PanelSpec):
        return panel

    coef_voc = _f(
        getattr(panel, "coef_voc_pct_c",
            getattr(panel, "coef_voc",
                getattr(panel, "tc_voc_pct_c", -0.28))),
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


# ================================
# Motor principal de strings
# ================================

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
        return {"ok": False, "errores": ["n_paneles_total inválido (<=0)."]}

    tmin = _f(t_min_c)
    t_oper = _f(t_oper_c, 55.0) if t_oper_c is not None else 55.0

    p = _as_panel_spec(panel)
    inv = _as_inversor_spec(inversor)

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
        return {"ok": False, "errores": errores, "warnings": warnings}

    out = calcular_strings_fv(
        n_paneles_total=n_total,
        panel=p,
        inversor=inv,
        t_min_c=tmin,
        dos_aguas=bool(dos_aguas),
        objetivo_dc_ac=objetivo_dc_ac,
        pdc_kw_objetivo=pdc_kw_objetivo,
        t_oper_c=t_oper,
    ) or {}

    out.setdefault("ok", False)
    out.setdefault("errores", [])
    out.setdefault("warnings", [])

    return out


# ================================
# Entrada desde CORE
# ================================

def ejecutar_paneles_desde_sizing(p, sizing):

    from electrical.catalogos.catalogos import get_panel, get_inversor

    equipos = getattr(p, "equipos", {}) or {}

    panel_id = equipos.get("panel_id")
    inversor_id = equipos.get("inversor_id")

    if not panel_id:
        raise ValueError("Panel no seleccionado.")

    if not inversor_id:
        raise ValueError("Inversor no seleccionado.")

    panel = get_panel(panel_id)
    inversor = get_inversor(inversor_id)

    # 🔒 sizing ahora es ResultadoSizing (dataclass fuerte)
    return ejecutar_calculo_strings(
        n_paneles_total=sizing.n_paneles,
        panel=panel,
        inversor=inversor,
        t_min_c=float(getattr(p, "t_min_c", 10.0)),
        dos_aguas=bool(getattr(p, "dos_aguas", False)),
        pdc_kw_objetivo=sizing.pdc_kw,
    )
