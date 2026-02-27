# Dimensionado energético FV: convierte consumo + cobertura + HSP + PR en kWp requerido y número de paneles.
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PanelSizingResultado:
    ok: bool
    errores: List[str]

    consumo_anual_kwh: float
    kwh_obj_anual: float
    cobertura_obj: float  # 0..1

    hsp_12m: List[float]  # kWh/m²/día por mes (≈ HSP)
    hsp_prom: float       # promedio anual (kWh/m²/día)
    pr: float             # performance ratio total (0..1)

    kwp_req: float
    n_paneles: int
    pdc_kw: float

    meta: Dict[str, Any]


_DIAS_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


# Limita un valor a un rango [lo, hi].
def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


# Convierte a float seguro con default.
def _safe_float(x: Any, default: float) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


# Convierte porcentaje (0..100) a factor multiplicativo (1 - pct/100).
def _pct_factor(pct: float) -> float:
    return 1.0 - float(pct) / 100.0


# Devuelve un perfil HSP mensual conservador (12 meses).
def _hsp_modelo_conservador_12m() -> List[float]:
    return [5.1, 5.4, 5.8, 5.6, 5.0, 4.5, 4.3, 4.4, 4.1, 4.0, 4.4, 4.7]


# Lee HSP mensual (12 valores) o usa un valor fijo, con opción de perfil conservador.
def _leer_hsp_12m(
    *,
    hsp_12m: Optional[List[float]] = None,
    hsp: Optional[float] = None,
    usar_modelo_conservador: bool = True,
) -> List[float]:
    if isinstance(hsp_12m, (list, tuple)) and len(hsp_12m) == 12:
        out: List[float] = []
        for v in hsp_12m:
            out.append(_clamp(_safe_float(v, 4.5), 0.5, 9.0))
        return out

    if usar_modelo_conservador:
        return _hsp_modelo_conservador_12m()

    h = _clamp(_safe_float(hsp, 4.5), 0.5, 9.0)
    return [h] * 12


# Calcula PR total (0..1) a partir de pérdidas base + sombras + pérdidas globales opcionales.
def _leer_pr(
    *,
    sombras_pct: float = 0.0,
    perdidas_sistema_pct: Optional[float] = None,
    perdidas_detalle: Optional[Dict[str, float]] = None,
) -> float:
    sombras_pct = _clamp(_safe_float(sombras_pct, 0.0), 0.0, 95.0)

    # Pérdidas típicas (fracciones, no %)
    base = {
        "temperatura": 0.07,
        "soiling": 0.03,
        "mismatch": 0.015,
        "dc": 0.02,
        "inversor": 0.03,
        "ac": 0.01,
        "disponibilidad": 0.01,
    }

    # Sobrescribe pérdidas base si el usuario pasa detalle.
    if isinstance(perdidas_detalle, dict):
        for k, v in perdidas_detalle.items():
            if k in base:
                base[k] = _clamp(_safe_float(v, base[k]), 0.0, 0.50)

    pr = 1.0
    for v in base.values():
        pr *= (1.0 - float(v))

    # Sombras se modela como pérdida adicional (multiplicativa).
    pr *= _pct_factor(sombras_pct)

    # Pérdidas globales del sistema (si se usa, se aplica directo como multiplicador).
    if perdidas_sistema_pct is not None:
        pr *= _pct_factor(_clamp(_safe_float(perdidas_sistema_pct, 0.0), 0.0, 95.0))

    return _clamp(pr, 0.55, 0.95)


# Calcula kWp requerido anual para producir kWh objetivo, usando HSP mensual y PR.
def _kwp_req_anual(kwh_obj_anual: float, hsp_12m: List[float], pr: float) -> float:
    prod_anual_por_kwp = 0.0
    for hsp_dia, dias in zip(hsp_12m, _DIAS_MES):
        prod_anual_por_kwp += float(hsp_dia) * float(pr) * float(dias)

    if prod_anual_por_kwp <= 0:
        raise ValueError("Producción anual por kWp inválida (<=0).")

    if float(kwh_obj_anual) <= 0:
        raise ValueError("kwh_obj_anual inválido (<=0).")

    return float(kwh_obj_anual) / prod_anual_por_kwp


# Convierte kWp requerido a número de paneles por potencia del panel (W).
def _n_paneles(kwp_req: float, panel_w: float) -> int:
    if panel_w <= 0:
        raise ValueError("Panel inválido (W<=0).")
    if kwp_req <= 0:
        raise ValueError("kwp_req inválido (<=0).")
    return max(1, int(ceil((float(kwp_req) * 1000.0) / float(panel_w))))


# Calcula potencia DC instalada (kW) por cantidad de paneles y potencia nominal (W).
def _pdc_kw(n_paneles: int, panel_w: float) -> float:
    return (int(n_paneles) * float(panel_w)) / 1000.0


# Normaliza cobertura: acepta 0..1 o 0..100.
def _normalizar_cobertura(cobertura_obj: Any) -> float:
    cov = _safe_float(cobertura_obj, 1.0)
    if cov > 1.0 and cov <= 100.0:
        cov = cov / 100.0
    return _clamp(cov, 0.0, 1.0)


# API pública: dimensiona sistema FV por energía (kWh) y cobertura deseada.
# API pública: dimensiona sistema FV por energía (kWh) y cobertura deseada.
def calcular_panel_sizing(
    *,
    consumo_12m_kwh: List[float],
    cobertura_obj: float,
    panel_w: float,
    hsp_12m: Optional[List[float]] = None,
    hsp: Optional[float] = None,
    usar_modelo_conservador: bool = True,
    usar_modelo_hn_conservador: Optional[bool] = None,  # ✅ alias legacy
    sombras_pct: float = 0.0,
    perdidas_sistema_pct: Optional[float] = None,
    perdidas_detalle: Optional[Dict[str, float]] = None,
    **_extra,  # ✅ ignora kwargs basura que puedan venir de UI vieja
) -> PanelSizingResultado:

    errores: List[str] = []

    # --- compatibilidad legacy ---
    if usar_modelo_hn_conservador is not None:
        usar_modelo_conservador = bool(usar_modelo_hn_conservador)

    # ==============================
    # Validación consumo 12m
    # ==============================
    if not isinstance(consumo_12m_kwh, list) or len(consumo_12m_kwh) != 12:
        errores.append("consumo_12m_kwh debe ser lista de 12 valores.")
        consumo = [0.0] * 12
    else:
        consumo = [_safe_float(x, 0.0) for x in consumo_12m_kwh]

    # Cobertura
    cov = _normalizar_cobertura(cobertura_obj)
    if cov <= 0:
        errores.append("cobertura_obj inválida (<=0).")

    # Potencia panel
    try:
        panel_w_f = float(panel_w)
        if panel_w_f <= 0:
            errores.append("panel_w inválido (<=0).")
    except Exception:
        panel_w_f = 0.0
        errores.append("panel_w inválido (no numérico).")

    # ==============================
    # HSP y PR
    # ==============================
    hsp12 = _leer_hsp_12m(
        hsp_12m=hsp_12m,
        hsp=hsp,
        usar_modelo_conservador=usar_modelo_conservador,
    )

    hsp_prom = sum(hsp12) / 12.0

    pr = _leer_pr(
        sombras_pct=sombras_pct,
        perdidas_sistema_pct=perdidas_sistema_pct,
        perdidas_detalle=perdidas_detalle,
    )

    consumo_anual = float(sum(consumo))
    if consumo_anual <= 0:
        errores.append("consumo_anual_kwh inválido (<=0).")

    kwh_obj_anual = consumo_anual * cov

    kwp_req = 0.0
    n_pan = 0
    pdc = 0.0

    if not errores:
        try:
            kwp_req = _kwp_req_anual(kwh_obj_anual, hsp12, pr)
            n_pan = _n_paneles(kwp_req, panel_w_f)
            pdc = _pdc_kw(n_pan, panel_w_f)
        except Exception as e:
            errores.append(str(e))

    ok = len(errores) == 0

    meta = {
        "dias_mes": list(_DIAS_MES),
        "hsp_fuente": "hsp_12m"
        if (isinstance(hsp_12m, (list, tuple)) and len(hsp_12m) == 12)
        else ("CONSERVADOR_12M" if usar_modelo_conservador else "hsp"),
        "sombras_pct": float(_clamp(_safe_float(sombras_pct, 0.0), 0.0, 95.0)),
        "perdidas_sistema_pct": None
        if perdidas_sistema_pct is None
        else float(_clamp(_safe_float(perdidas_sistema_pct, 0.0), 0.0, 95.0)),
        "perdidas_detalle_usadas": dict(perdidas_detalle)
        if isinstance(perdidas_detalle, dict)
        else {},
    }

    return PanelSizingResultado(
        ok=ok,
        errores=errores,
        consumo_anual_kwh=consumo_anual,
        kwh_obj_anual=kwh_obj_anual,
        cobertura_obj=cov,
        hsp_12m=hsp12,
        hsp_prom=float(hsp_prom),
        pr=float(pr),
        kwp_req=float(kwp_req),
        n_paneles=int(n_pan),
        pdc_kw=float(pdc),
        meta=meta,
    )
        meta=meta,
    )
