from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .calculo_de_strings import PanelSpec, InversorSpec, calcular_strings_fv


# -----------------------
# Modelos UI (compat)
# -----------------------
@dataclass(frozen=True)
class PanelFV:
    voc_stc: float
    vmp_stc: float
    isc: float
    imp: float
    coef_voc_pct_c: float  # ej -0.28 (%/°C)
    pmax_w: float = 0.0    # opcional


@dataclass(frozen=True)
class InversorFV:
    vdc_max: float
    mppt_min: float
    mppt_max: float
    imppt_max: float
    n_mppt: int
    pac_kw: float = 0.0    # opcional


# -----------------------
# Utilitarios internos
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


def _to_panel_spec(panel: PanelFV) -> PanelSpec:
    return PanelSpec(
        pmax_w=_f(panel.pmax_w, 0.0),
        vmp_v=_f(panel.vmp_stc, 0.0),
        voc_v=_f(panel.voc_stc, 0.0),
        imp_a=_f(panel.imp, 0.0),
        isc_a=_f(panel.isc, 0.0),
        coef_voc_pct_c=_f(panel.coef_voc_pct_c, -0.28),
    )


def _to_inversor_spec(inv: InversorFV) -> InversorSpec:
    n_mppt = _i(inv.n_mppt, 1) or 1
    return InversorSpec(
        pac_kw=_f(inv.pac_kw, 0.0),
        vdc_max_v=_f(inv.vdc_max, 0.0),
        mppt_min_v=_f(inv.mppt_min, 0.0),
        mppt_max_v=_f(inv.mppt_max, 0.0),
        n_mppt=n_mppt,
        imppt_max_a=_f(inv.imppt_max, 0.0),
    )


# -----------------------
# API pública
# -----------------------
def validar_string(
    panel: PanelFV,
    inversor: InversorFV,
    n_paneles_total: int,
    temp_min: float,
) -> Dict[str, Any]:
    """
    Wrapper de compatibilidad UI:
    - UI pasa n_paneles_total y temp_min
    - Se llama al motor (calculo_de_strings) y se reporta validez:
      Voc frío <= vdc_max, Vmp dentro de MPPT, corriente <= imppt_max.
    """
    warnings: List[str] = []
    errores: List[str] = []

    n_total = _i(n_paneles_total, 0)
    if n_total <= 0:
        return {
            "string_valido": False,
            "ok_vdc": False,
            "ok_mppt": False,
            "ok_corriente": False,
            "errores": ["n_paneles_total inválido (<=0)."],
            "warnings": [],
            "meta": {},
        }

    tmin = _f(temp_min, None)  # type: ignore[arg-type]
    if tmin is None:  # por si viene algo imposible (NaN textual, etc.)
        return {
            "string_valido": False,
            "ok_vdc": False,
            "ok_mppt": False,
            "ok_corriente": False,
            "errores": ["temp_min inválido (no convertible a número)."],
            "warnings": [],
            "meta": {},
        }
    # _f con default None no sirve directamente; hacemos try real:
    try:
        tmin = float(temp_min)
    except Exception:
        return {
            "string_valido": False,
            "ok_vdc": False,
            "ok_mppt": False,
            "ok_corriente": False,
            "errores": ["temp_min inválido (no convertible a número)."],
            "warnings": [],
            "meta": {},
        }

    p = _to_panel_spec(panel)
    inv = _to_inversor_spec(inversor)

    # Coherencia mínima (no NEC)
    if p.voc_v <= 0 or p.vmp_v <= 0:
        errores.append("Panel inválido: voc_stc/vmp_stc deben ser > 0.")
    if inv.vdc_max_v <= 0 or inv.mppt_min_v <= 0 or inv.mppt_max_v <= 0:
        errores.append("Inversor inválido: vdc_max/mppt_min/mppt_max deben ser > 0.")
    if inv.mppt_min_v >= inv.mppt_max_v:
        errores.append("Inversor inválido: mppt_min debe ser < mppt_max.")
    if inv.imppt_max_a <= 0:
        errores.append("Inversor inválido: imppt_max debe ser > 0.")

    if errores:
        return {
            "string_valido": False,
            "ok_vdc": False,
            "ok_mppt": False,
            "ok_corriente": False,
            "errores": errores,
            "warnings": warnings,
            "meta": {"n_paneles_total": n_total, "t_min_c": tmin},
        }

    # Llamada al motor
    res = calcular_strings_fv(
        n_paneles_total=n_total,
        panel=p,
        inversor=inv,
        t_min_c=tmin,
        dos_aguas=False,
    ) or {}

    if not res.get("ok", False):
        # Mantener separación errores/warnings
        warnings = list(res.get("warnings") or [])
        errores = list(res.get("errores") or [])
        return {
            "string_valido": False,
            "ok_vdc": False,
            "ok_mppt": False,
            "ok_corriente": False,
            "errores": errores,
            "warnings": warnings,
            "meta": res.get("meta") or {},
        }

    r = res.get("recomendacion") or {}

    # Valores recomendados por el motor (tolerante a nombres)
    voc_frio_total = _f(r.get("voc_frio_string_v", 0.0), 0.0)
    vmp_operativo = _f(r.get("vmp_string_v", 0.0), 0.0)
    corriente_mppt = _f(r.get("i_mppt_a", r.get("imppt_a", 0.0)), 0.0)

    ok_vdc = (voc_frio_total > 0.0) and (voc_frio_total <= inv.vdc_max_v + 1e-9)
    ok_mppt = (vmp_operativo >= inv.mppt_min_v - 1e-9) and (vmp_operativo <= inv.mppt_max_v + 1e-9)
    ok_corr = corriente_mppt <= inv.imppt_max_a + 1e-9

    # meta uniforme (una sola verdad)
    ns_recomendado = _i(r.get("n_series", r.get("n_paneles_string", r.get("ns", 0))), 0)
    n_strings_total = _i(r.get("n_strings_total", r.get("n_strings", 0)), 0)

    return {
        "voc_frio_total": voc_frio_total,
        "vmp_operativo": vmp_operativo,
        "corriente_mppt": corriente_mppt,
        "ok_vdc": bool(ok_vdc),
        "ok_mppt": bool(ok_mppt),
        "ok_corriente": bool(ok_corr),
        "string_valido": bool(ok_vdc and ok_mppt and ok_corr),
        "errores": [],
        "warnings": list(res.get("warnings") or []),
        "meta": {
            "n_paneles_total": n_total,
            "t_min_c": tmin,
            "ns_recomendado": ns_recomendado,
            "n_strings_total": n_strings_total,
            **(res.get("meta") or {}),
        },
    }
