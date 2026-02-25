# Entradas del dominio paneles: normaliza payload de UI/API para strings sin hacer cálculos eléctricos.
from __future__ import annotations

from typing import Any, Dict, Optional


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


# Limita un float a un rango para evitar payloads absurdos desde UI.
def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


# Construye payload normalizado para el orquestador de strings en modo objetivo (kWdc o DC/AC).
def build_strings_payload(
    *,
    panel: Any,
    inversor: Any,
    n_paneles_total: Optional[int] = None,
    t_min_c: float,
    dos_aguas: bool,
    objetivo_dc_ac: Optional[float] = 1.2,
    pdc_kw_objetivo: Optional[float] = None,
    t_oper_c: Optional[float] = 55.0,
) -> Dict[str, Any]:
    n_total = _i(n_paneles_total, 0) if n_paneles_total is not None else None

    tmin = _f(t_min_c, 0.0)
    # rango razonable de temperatura ambiente mínima (ajústalo si quieres)
    tmin = _clamp(tmin, -40.0, 40.0)

    toper = _f(t_oper_c, 55.0) if t_oper_c is not None else None
    # rango razonable de temperatura de célula/módulo
    if toper is not None:
        toper = _clamp(toper, 25.0, 85.0)

    odc = _f(objetivo_dc_ac, 1.2) if objetivo_dc_ac is not None else None
    # rango típico de DC/AC objetivo (evita 0 o 10 por error UI)
    if odc is not None:
        odc = _clamp(odc, 0.8, 1.6)

    # Importante: si no viene objetivo, se queda None (no se convierte a 0.0).
    pdc_obj = _f(pdc_kw_objetivo, 0.0) if pdc_kw_objetivo is not None else None
    if pdc_obj is not None and pdc_obj <= 0:
        # 0 o negativo no es un objetivo válido, lo tratamos como None.
        pdc_obj = None

    return {
        "panel": panel,
        "inversor": inversor,
        "n_paneles_total": n_total,
        "t_min_c": float(tmin),
        "t_oper_c": float(toper) if toper is not None else None,
        "dos_aguas": bool(dos_aguas),
        "objetivo_dc_ac": float(odc) if odc is not None else None,
        "pdc_kw_objetivo": float(pdc_obj) if pdc_obj is not None else None,
    }
