# core/sistema_fv_mapper.py
from __future__ import annotations

from typing import Any, Dict, List


# =========================
# helpers seguros
# =========================
def _to_float(x: Any, default: float) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _pct_to_factor(pct: float) -> float:
    return 1.0 - pct / 100.0


# =========================
# API PUBLICA (LA QUE IMPORTA)
# =========================
def construir_parametros_fv_desde_dict(sfv: dict) -> Dict[str, Any]:
    """
    Convierte datos del Paso 3 (UI) en parámetros numéricos limpios
    que consume el motor FV.
    """

    if not isinstance(sfv, dict):
        sfv = {}

    # --- entradas ---
    hsp = _clamp(_to_float(sfv.get("hsp"), 4.8), 0.5, 9.0)

    perdidas_pct = _clamp(_to_float(sfv.get("perdidas_sistema_pct"), 14.0), 0.0, 60.0)
    sombras_pct = _clamp(_to_float(sfv.get("sombras_pct"), 0.0), 0.0, 80.0)

    tipo_superficie = str(sfv.get("tipo_superficie") or "plano").lower()
    inclinacion_deg = _clamp(_to_float(sfv.get("inclinacion_deg"), 15.0), 0.0, 60.0)

    azimut_deg = _clamp(_to_float(sfv.get("azimut_deg"), 180.0), 0.0, 359.9)

    # --- dos aguas ---
    azimut_a_deg = None
    azimut_b_deg = None
    reparto_pct_a = None

    if tipo_superficie == "dos_aguas":
        azimut_a_deg = _clamp(_to_float(sfv.get("azimut_a_deg"), azimut_deg), 0.0, 359.9)
        azimut_b_deg = _clamp(
            _to_float(sfv.get("azimut_b_deg"), (azimut_a_deg + 180) % 360),
            0.0,
            359.9,
        )
        reparto_pct_a = _clamp(_to_float(sfv.get("reparto_pct_a"), 50.0), 0.0, 100.0)
        azimut_deg = azimut_a_deg

    # --- producción base ---
    pr = _pct_to_factor(perdidas_pct) * _pct_to_factor(sombras_pct)
    pr = _clamp(pr, 0.1, 1.0)

    prod_base_kwh_kwp_mes = hsp * 30.0 * pr

    # --- factores mensuales ---
    factores = [1.0] * 12

    out = {
        "hsp": float(hsp),
        "prod_base_kwh_kwp_mes": float(prod_base_kwh_kwp_mes),
        "factores_fv_12m": factores,
        "azimut_deg": float(azimut_deg),
        "inclinacion_deg": float(inclinacion_deg),
        "tipo_superficie": tipo_superficie,
        "perdidas_sistema_pct": float(perdidas_pct),
        "sombras_pct": float(sombras_pct),
    }

    if tipo_superficie == "dos_aguas":
        out.update(
            {
                "azimut_a_deg": float(azimut_a_deg),
                "azimut_b_deg": float(azimut_b_deg),
                "reparto_pct_a": float(reparto_pct_a),
            }
        )

    return out
