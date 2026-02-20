# electrical/sizing_electric.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


# ==========================================================
# Modelos mínimos (API estable para core/sizing.py)
# ==========================================================
@dataclass(frozen=True)
class SizingInput:
    consumo_anual_kwh: float
    produccion_anual_por_kwp_kwh: float
    cobertura_obj: float
    dc_ac_obj: float
    pmax_panel_w: float  # trazabilidad (v1 no lo usa para ranking)


@dataclass(frozen=True)
class InversorCandidato:
    id: str
    pac_kw: float
    n_mppt: int
    mppt_min_v: float
    mppt_max_v: float
    vdc_max_v: float


# ==========================================================
# API pública
# ==========================================================
def ejecutar_sizing(*, inp: SizingInput, inversores_catalogo: List[InversorCandidato]) -> Dict[str, Any]:
    """
    Selección automática de inversor (v1, robusta):

    1) Calcula Pdc requerido por energía:
       Pdc_req = (Consumo_anual * cobertura) / (Prod_anual_por_kwp)

    2) Define Pac objetivo por DC/AC:
       Pac_obj = Pdc_req / dc_ac_obj

    3) Rankea candidatos:
       - Penaliza fuerte si pac_kw < Pac_obj
       - Prefiere el más cercano por encima (oversize pequeño)
       - Bonus por #MPPT

    Retorna:
      {
        "inversor_recomendado": <id>,
        "inversor_recomendado_meta": {
            "pdc_req_kw": ...,
            "pac_obj_kw": ...,
            "dc_ac_obj": ...,
            "candidatos": [ {id, pac_kw, n_mppt, ... , score}, ... ]
        }
      }
    """
    invs = list(inversores_catalogo or [])
    if not invs:
        raise ValueError("Catálogo de inversores vacío.")

    pdc_req_kw = _pdc_req_kw(
        consumo_anual_kwh=inp.consumo_anual_kwh,
        produccion_anual_por_kwp_kwh=inp.produccion_anual_por_kwp_kwh,
        cobertura_obj=inp.cobertura_obj,
    )
    dc_ac = _clamp(inp.dc_ac_obj, 1.0, 2.0)
    pac_obj_kw = pdc_req_kw / dc_ac if dc_ac > 0 else 0.0

    ranked = [_rank_inv(inv, pac_obj_kw) for inv in invs]
    ranked.sort(key=lambda x: x["score"], reverse=True)

    best = ranked[0]
    meta = {
        "pdc_req_kw": round(float(pdc_req_kw), 3),
        "pac_obj_kw": round(float(pac_obj_kw), 3),
        "dc_ac_obj": round(float(dc_ac), 3),
        "candidatos": ranked[:12],
    }
    return {
        "inversor_recomendado": str(best["id"]),
        "inversor_recomendado_meta": meta,
    }


# ==========================================================
# Helpers (cortos)
# ==========================================================
def _pdc_req_kw(*, consumo_anual_kwh: float, produccion_anual_por_kwp_kwh: float, cobertura_obj: float) -> float:
    prod = float(produccion_anual_por_kwp_kwh)
    if prod <= 0:
        raise ValueError("produccion_anual_por_kwp_kwh inválida (<=0).")
    cov = _clamp(float(cobertura_obj), 0.0, 1.0)
    return (float(consumo_anual_kwh) * cov) / prod


def _rank_inv(inv: InversorCandidato, pac_obj_kw: float) -> Dict[str, Any]:
    pac = float(inv.pac_kw)
    obj = float(pac_obj_kw)

    score = _score_pac(pac, obj) + 2.0 * float(inv.n_mppt)
    return {
        "id": str(inv.id),
        "pac_kw": round(pac, 3),
        "n_mppt": int(inv.n_mppt),
        "mppt_min_v": float(inv.mppt_min_v),
        "mppt_max_v": float(inv.mppt_max_v),
        "vdc_max_v": float(inv.vdc_max_v),
        "score": round(float(score), 3),
    }


def _score_pac(pac: float, obj: float) -> float:
    if pac <= 0:
        return -1e9
    if obj <= 0:
        return 0.0

    ratio = pac / obj
    if ratio < 1.0:
        return 100.0 * ratio - 200.0  # queda corto => muy penalizado

    # queda por encima: preferimos ratio cercano a 1.0
    return 100.0 - 20.0 * (ratio - 1.0)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))
