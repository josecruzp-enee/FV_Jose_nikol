from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Dict, List, Optional


# ==========================================================
# Modelos de salida (estables y simples)
# ==========================================================
@dataclass(frozen=True)
class PanelSizingResultado:
    ok: bool
    errores: List[str]

    # energía/objetivo
    consumo_anual_kwh: float
    kwh_obj_anual: float
    cobertura_obj: float  # 0..1

    # recurso y pérdidas
    hsp_12m: List[float]  # kWh/m²/día por mes (≈ HSP)
    hsp_prom: float       # promedio anual (kWh/m²/día)
    pr: float             # performance ratio total (0..1)

    # sizing
    kwp_req: float
    n_paneles: int
    pdc_kw: float

    # trazabilidad
    meta: Dict[str, Any]


# ==========================================================
# Utilitarios
# ==========================================================
def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def _safe_float(x: Any, default: float) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _pct_factor(pct: float) -> float:
    return 1.0 - float(pct) / 100.0


_DIAS_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _hsp_modelo_conservador_12m() -> List[float]:
    """
    Modelo offline conservador (Centroamérica/latitudes tropicales).
    Ajustable luego por ubicación, pero estable como fallback.
    """
    return [
        5.1,  # Ene
        5.4,  # Feb
        5.8,  # Mar
        5.6,  # Abr
        5.0,  # May
        4.5,  # Jun
        4.3,  # Jul
        4.4,  # Ago
        4.1,  # Sep
        4.0,  # Oct
        4.4,  # Nov
        4.7,  # Dic
    ]


def _leer_hsp_12m(
    *,
    hsp_12m: Optional[List[float]] = None,
    hsp: Optional[float] = None,
    usar_modelo_conservador: bool = True,
) -> List[float]:
    # 1) si viene lista 12m válida
    if isinstance(hsp_12m, (list, tuple)) and len(hsp_12m) == 12:
        out: List[float] = []
        for v in hsp_12m:
            out.append(_clamp(_safe_float(v, 4.5), 0.5, 9.0))
        return out

    # 2) modelo offline conservador
    if usar_modelo_conservador:
        return _hsp_modelo_conservador_12m()

    # 3) fallback a hsp único
    h = _clamp(_safe_float(hsp, 4.5), 0.5, 9.0)
    return [h] * 12


def _leer_pr(
    *,
    sombras_pct: float = 0.0,
    perdidas_sistema_pct: Optional[float] = None,
    perdidas_detalle: Optional[Dict[str, float]] = None,
) -> float:
    """
    PR físico simplificado, conservador.
    - pérdidas base constantes (editables vía perdidas_detalle)
    - sombras siempre multiplican
    - si perdidas_sistema_pct viene, se aplica suave (30%) para compat
    """
    sombras_pct = _clamp(_safe_float(sombras_pct, 0.0), 0.0, 95.0)

    base = {
        "temperatura": 0.07,
        "soiling": 0.03,
        "mismatch": 0.015,
        "dc": 0.02,
        "inversor": 0.03,
        "ac": 0.01,
        "disponibilidad": 0.01,
    }

    if isinstance(perdidas_detalle, dict):
        for k, v in perdidas_detalle.items():
            if k in base:
                base[k] = _clamp(_safe_float(v, base[k]), 0.0, 0.50)

    pr = 1.0
    for v in base.values():
        pr *= (1.0 - float(v))

    pr *= _pct_factor(sombras_pct)

    if perdidas_sistema_pct is not None:
        pr *= _pct_factor(_clamp(_safe_float(perdidas_sistema_pct, 0.0), 0.0, 95.0) * 0.3)

    return _clamp(pr, 0.55, 0.95)


def _kwp_req_anual(kwh_obj_anual: float, hsp_12m: List[float], pr: float) -> float:
    prod_anual_por_kwp = 0.0
    for hsp_dia, dias in zip(hsp_12m, _DIAS_MES):
        prod_anual_por_kwp += float(hsp_dia) * float(pr) * float(dias)

    if prod_anual_por_kwp <= 0:
        raise ValueError("Producción anual por kWp inválida (<=0).")

    return float(kwh_obj_anual) / prod_anual_por_kwp


def _n_paneles(kwp_req: float, panel_w: float) -> int:
    if panel_w <= 0:
        raise ValueError("Panel inválido (W<=0).")
    return max(1, int(ceil((float(kwp_req) * 1000.0) / float(panel_w))))


def _pdc_kw(n_paneles: int, panel_w: float) -> float:
    return (int(n_paneles) * float(panel_w)) / 1000.0


def _normalizar_cobertura(cobertura_obj: Any) -> float:
    """
    Acepta:
      - 0..1 (fracción)
      - 0..100 (porcentaje)
    """
    cov = _safe_float(cobertura_obj, 1.0)
    if cov > 1.0 and cov <= 100.0:
        cov = cov / 100.0
    return _clamp(cov, 0.0, 1.0)


# ==========================================================
# API pública
# ==========================================================
def calcular_panel_sizing(
    *,
    consumo_12m_kwh: List[float],
    cobertura_obj: float,
    panel_w: float,
    # recurso solar
    hsp_12m: Optional[List[float]] = None,
    hsp: Optional[float] = None,
    usar_modelo_conservador: bool = True,
    # pérdidas/pr
    sombras_pct: float = 0.0,
    perdidas_sistema_pct: Optional[float] = None,
    perdidas_detalle: Optional[Dict[str, float]] = None,
) -> PanelSizingResultado:
    errores: List[str] = []

    if not isinstance(consumo_12m_kwh, list) or len(consumo_12m_kwh) != 12:
        errores.append("consumo_12m_kwh debe ser lista de 12 valores.")
        consumo = [0.0] * 12
    else:
        consumo = [_safe_float(x, 0.0) for x in consumo_12m_kwh]

    cov = _normalizar_cobertura(cobertura_obj)

    try:
        panel_w_f = float(panel_w)
        if panel_w_f <= 0:
            errores.append("panel_w inválido (<=0).")
    except Exception:
        panel_w_f = 0.0
        errores.append("panel_w inválido (no numérico).")

    hsp12 = _leer_hsp_12m(hsp_12m=hsp_12m, hsp=hsp, usar_modelo_conservador=usar_modelo_conservador)
    hsp_prom = sum(hsp12) / 12.0

    pr = _leer_pr(
        sombras_pct=sombras_pct,
        perdidas_sistema_pct=perdidas_sistema_pct,
        perdidas_detalle=perdidas_detalle,
    )

    consumo_anual = float(sum(consumo))
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
        "hsp_fuente": "hsp_12m" if (isinstance(hsp_12m, (list, tuple)) and len(hsp_12m) == 12) else ("CONSERVADOR_12M" if usar_modelo_conservador else "hsp"),
        "perdidas_detalle_usadas": perdidas_detalle if isinstance(perdidas_detalle, dict) else {},
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
