from __future__ import annotations

from math import ceil
from typing import Dict, List


def evaluar_balance_horario(
    *,
    demanda_24h: Dict[int, float],
    fv_24h: Dict[int, float],
    tarifa_compra_l_kwh: float,
    precio_inyeccion_l_kwh: float,
) -> dict:

    autoconsumo = 0.0
    excedente = 0.0
    compra_red = 0.0

    for h in range(24):
        d = float(demanda_24h.get(h, 0.0) or 0.0)
        f = float(fv_24h.get(h, 0.0) or 0.0)

        autoconsumo += min(d, f)
        excedente += max(f - d, 0.0)
        compra_red += max(d - f, 0.0)

    valor_autoconsumo = autoconsumo * tarifa_compra_l_kwh
    valor_inyeccion = excedente * precio_inyeccion_l_kwh

    return {
        "autoconsumo_kwh_dia": autoconsumo,
        "excedente_kwh_dia": excedente,
        "compra_red_kwh_dia": compra_red,
        "valor_autoconsumo_l_dia": valor_autoconsumo,
        "valor_inyeccion_l_dia": valor_inyeccion,
        "beneficio_l_dia": valor_autoconsumo + valor_inyeccion,
    }


def construir_fv_24h_desde_kwp(
    *,
    perfil_fv_unitario_24h: Dict[int, float],
    kwp: float,
) -> Dict[int, float]:

    return {
        h: float(perfil_fv_unitario_24h.get(h, 0.0) or 0.0) * kwp
        for h in range(24)
    }


def optimizar_kwp_autoconsumo_inyeccion(
    *,
    demanda_24h: Dict[int, float],
    perfil_fv_unitario_24h: Dict[int, float],
    panel_w: float,
    tarifa_compra_l_kwh: float,
    precio_inyeccion_l_kwh: float = 2.20,
    kwp_min: float = 1.0,
    kwp_max: float = 500.0,
    paso_kwp: float = 1.0,
    mejora_minima_l_dia: float = 5.0,
) -> dict:

    mejor = None
    anterior = None

    kwp = kwp_min

    while kwp <= kwp_max:

        fv_24h = construir_fv_24h_desde_kwp(
            perfil_fv_unitario_24h=perfil_fv_unitario_24h,
            kwp=kwp,
        )

        r = evaluar_balance_horario(
            demanda_24h=demanda_24h,
            fv_24h=fv_24h,
            tarifa_compra_l_kwh=tarifa_compra_l_kwh,
            precio_inyeccion_l_kwh=precio_inyeccion_l_kwh,
        )

        r["kwp"] = kwp
        r["n_paneles"] = int(ceil((kwp * 1000.0) / panel_w))
        r["pdc_kw"] = r["n_paneles"] * panel_w / 1000.0

        if anterior is not None:
            r["beneficio_marginal_l_dia"] = (
                r["beneficio_l_dia"] -
                anterior["beneficio_l_dia"]
            )
        else:
            r["beneficio_marginal_l_dia"] = r["beneficio_l_dia"]

        if mejor is None:
            mejor = r

        if r["beneficio_l_dia"] > mejor["beneficio_l_dia"]:
            mejor = r

        if anterior is not None:
            if r["beneficio_marginal_l_dia"] < mejora_minima_l_dia:
                break

        anterior = r
        kwp += paso_kwp

    return mejor
