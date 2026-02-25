# Entradas del dominio paneles: normaliza payload de UI/API para dimensionado y strings sin hacer cálculos eléctricos.
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


# Construye payload normalizado para el orquestador de cálculo de strings en modo objetivo (kWdc/DC-AC).
def build_strings_payload(
    *,
    panel: Any,
    inversor: Any,
    # Inventario derivado del sizing (si existe); no es la entrada principal del usuario.
    n_paneles_total: Optional[int] = None,
    # Temperatura mínima ambiente para Voc frío.
    t_min_c: float,
    # Topología geométrica (si hay 2 MPPT y dos aguas, reparte strings).
    dos_aguas: bool,
    # Objetivo de sobredimensionamiento DC/AC (si no se provee kWdc objetivo).
    objetivo_dc_ac: Optional[float] = 1.2,
    # Objetivo directo de potencia DC (kW) proveniente del dimensionado energético.
    pdc_kw_objetivo: Optional[float] = None,
    # Temperatura operativa del módulo para validar MPPT_min con Vmp caliente (conservador por defecto).
    t_oper_c: Optional[float] = 55.0,
) -> Dict[str, Any]:
    return {
        "panel": panel,
        "inversor": inversor,
        "n_paneles_total": _i(n_paneles_total, 0) if n_paneles_total is not None else None,
        "t_min_c": _f(t_min_c, 0.0),
        "t_oper_c": _f(t_oper_c, 55.0) if t_oper_c is not None else None,
        "dos_aguas": bool(dos_aguas),
        "objetivo_dc_ac": _f(objetivo_dc_ac, 1.2) if objetivo_dc_ac is not None else None,
        "pdc_kw_objetivo": _f(pdc_kw_objetivo, 0.0) if pdc_kw_objetivo is not None else None,
    }
