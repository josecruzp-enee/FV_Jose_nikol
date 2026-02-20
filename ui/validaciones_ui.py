from __future__ import annotations

from typing import Any, List


def _as_dict(x: Any) -> dict:
    return x if isinstance(x, dict) else {}


def campos_faltantes_para_paso5(ctx: Any) -> List[str]:
    """Devuelve lista de prerequisitos UI faltantes para ejecutar ingeniería (Paso 5)."""
    faltantes: List[str] = []

    dc = _as_dict(getattr(ctx, "datos_cliente", {}))
    consumo = _as_dict(getattr(ctx, "consumo", {}))
    equipos = _as_dict(getattr(ctx, "equipos", {}))

    if not str(dc.get("cliente", "")).strip():
        faltantes.append("Paso 1: Nombre del cliente")
    if not str(dc.get("ubicacion", "")).strip():
        faltantes.append("Paso 1: Ubicación")

    tarifa = float(consumo.get("tarifa_energia_L_kwh", 0.0) or 0.0)
    if tarifa <= 0:
        faltantes.append("Paso 2: Tarifa energía (L/kWh) > 0")

    kwh_12m = consumo.get("kwh_12m", [])
    if not isinstance(kwh_12m, list) or len(kwh_12m) != 12:
        faltantes.append("Paso 2: 12 valores de consumo mensual")
    else:
        try:
            if max(float(x) for x in kwh_12m) <= 0:
                faltantes.append("Paso 2: Al menos un mes con consumo > 0 kWh")
        except Exception:
            faltantes.append("Paso 2: Consumo mensual numérico válido")

    if not equipos.get("panel_id"):
        faltantes.append("Paso 4: Seleccionar panel")
    if not equipos.get("inversor_id"):
        faltantes.append("Paso 4: Seleccionar inversor")

    return faltantes
