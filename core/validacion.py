# nucleo/validacion.py
from __future__ import annotations

from nucleo.modelo import modelo


def validar_entradas(p: DatosProyecto) -> None:
    if len(p.consumo_12m) != 12:
        raise ValueError("consumo_12m debe tener 12 valores (Ene..Dic)")
    if len(p.factores_fv_12m) != 12:
        raise ValueError("factores_fv_12m debe tener 12 valores (Ene..Dic)")

    if any(x < 0 for x in p.consumo_12m):
        raise ValueError("consumo_12m no puede tener negativos")
    if any(f <= 0 for f in p.factores_fv_12m):
        raise ValueError("factores_fv_12m deben ser > 0")

    if p.tarifa_energia <= 0:
        raise ValueError("tarifa_energia debe ser > 0")
    if p.cargos_fijos < 0:
        raise ValueError("cargos_fijos debe ser >= 0")

    if p.prod_base_kwh_kwp_mes <= 0:
        raise ValueError("prod_base_kwh_kwp_mes debe ser > 0")
    if not (0 < p.cobertura_objetivo <= 1):
        raise ValueError("cobertura_objetivo debe estar en (0, 1]")

    if p.costo_usd_kwp <= 0 or p.tcambio <= 0:
        raise ValueError("costo_usd_kwp y tcambio deben ser > 0")

    if not (0 <= p.tasa_anual < 1):
        raise ValueError("tasa_anual debe ser decimal (ej 0.16)")
    if p.plazo_anios <= 0:
        raise ValueError("plazo_anios debe ser > 0")
    if not (0 < p.porcentaje_financiado <= 1):
        raise ValueError("porcentaje_financiado debe estar en (0, 1]")

