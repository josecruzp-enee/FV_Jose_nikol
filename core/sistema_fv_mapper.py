# core/sistema_fv_mapper.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# =========================
# Helpers numéricos seguros
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
    # pct 0..100 -> factor 1..0
    return 1.0 - (pct / 100.0)


# =========================
# Contrato de salida (motor)
# =========================
@dataclass(frozen=True)
class ParametrosFV:
    hsp: float
    prod_base_kwh_kwp_mes: float
    factores_12m: List[float]

    # Geometría para trazabilidad (el motor puede ignorar si no aplica)
    azimut_deg: float
    inclinacion_deg: float
    tipo_superficie: str

    # Dos aguas (opcionales)
    azimut_a_deg: Optional[float] = None
    azimut_b_deg: Optional[float] = None
    reparto_pct_a: Optional[float] = None


# =========================
# API pública única
# =========================
def construir_parametros_fv_desde_ctx(ctx: Any) -> Dict[str, Any]:
    """
    Entradas: ctx (de wizard) con ctx.sistema_fv dict
    Salidas: dict limpio numérico para motor FV.

    REGLAS:
    - Mantiene compat: siempre devuelve azimut_deg.
    - Si tipo_superficie == 'dos_aguas', también devuelve azimut_a_deg, azimut_b_deg, reparto_pct_a.
    - Calcula prod_base_kwh_kwp_mes desde HSP y pérdidas + sombras (modelo simple y consistente).
    - factores_12m por defecto = [1]*12 (si luego metes estacionalidad, se actualiza aquí).
    """
    sfv = getattr(ctx, "sistema_fv", None) or {}
    if not isinstance(sfv, dict):
        sfv = {}

    # ---------
    # Entradas base
    # ---------
    hsp = _clamp(_to_float(sfv.get("hsp"), 4.8), 0.5, 9.0)

    perdidas_pct = _clamp(_to_float(sfv.get("perdidas_sistema_pct"), 14.0), 0.0, 60.0)
    sombras_pct = _clamp(_to_float(sfv.get("sombras_pct"), 0.0), 0.0, 80.0)

    tipo_superficie = str(sfv.get("tipo_superficie") or "plano").strip().lower()
    if tipo_superficie not in ("plano", "dos_aguas"):
        tipo_superficie = "plano"

    inclinacion_deg = _clamp(_to_float(sfv.get("inclinacion_deg"), 15.0), 0.0, 60.0)

    # azimut compat (si no viene, inferimos desde azimut_a o default sur=180)
    azimut_deg = _to_float(sfv.get("azimut_deg"), None)  # type: ignore[arg-type]
    if azimut_deg is None:
        azimut_deg = _to_float(sfv.get("azimut_a_deg"), 180.0)
    azimut_deg = _clamp(float(azimut_deg), 0.0, 359.9)

    # ---------
    # Dos aguas
    # ---------
    azimut_a_deg = azimut_b_deg = reparto_pct_a = None

    if tipo_superficie == "dos_aguas":
        azimut_a_deg = _clamp(_to_float(sfv.get("azimut_a_deg"), azimut_deg), 0.0, 359.9)
        azimut_b_deg = _clamp(_to_float(sfv.get("azimut_b_deg"), (azimut_a_deg + 180.0) % 360.0), 0.0, 359.9)
        reparto_pct_a = _clamp(_to_float(sfv.get("reparto_pct_a"), 50.0), 0.0, 100.0)

        # compat: azimut_deg representa el "azimut principal" (A)
        azimut_deg = azimut_a_deg

    # ---------
    # Modelo simple de producción base mensual por kWp
    # ---------
    # Base física aproximada:
    #   kWh/kWp/día ≈ HSP * PR
    #   kWh/kWp/mes ≈ HSP * 30 * PR
    #
    # PR (performance ratio) aquí se modela con pérdidas globales + sombras:
    pr = _pct_to_factor(perdidas_pct) * _pct_to_factor(sombras_pct)
    pr = _clamp(pr, 0.1, 1.0)

    prod_base_kwh_kwp_mes = hsp * 30.0 * pr  # estable, numérico, reproducible

    # ---------
    # Factores mensuales (si no hay estacionalidad todavía)
    # ---------
    factores_12m = sfv.get("factores_12m")
    if isinstance(factores_12m, list) and len(factores_12m) == 12:
        factores = [_clamp(_to_float(v, 1.0), 0.3, 1.7) for v in factores_12m]
    else:
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
                "azimut_a_deg": float(azimut_a_deg),   # type: ignore[arg-type]
                "azimut_b_deg": float(azimut_b_deg),   # type: ignore[arg-type]
                "reparto_pct_a": float(reparto_pct_a), # type: ignore[arg-type]
            }
        )

    return out
