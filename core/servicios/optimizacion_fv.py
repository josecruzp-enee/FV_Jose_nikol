from __future__ import annotations

from math import ceil
from typing import Dict, List


def construir_demanda_8760_desde_24h(
    demanda_24h: Dict[int, float],
    n_horas: int,
) -> List[float]:

    return [
        float(demanda_24h.get(i % 24, 0.0) or 0.0)
        for i in range(n_horas)
    ]


def construir_perfil_unitario_fv_8760(
    energia_horaria_kwh: List[float],
    pdc_kw_base: float,
) -> List[float]:

    if pdc_kw_base <= 0:
        raise ValueError("pdc_kw_base inválido")

    return [
        float(e or 0.0) / pdc_kw_base
        for e in energia_horaria_kwh
    ]


def evaluar_balance_8760(
    *,
    demanda_8760_kwh: List[float],
    fv_unitario_8760_kwh_kwp: List[float],
    kwp: float,
    tarifa_compra_l_kwh: float,
    precio_inyeccion_l_kwh: float,
) -> dict:

    autoconsumo = 0.0
    excedente = 0.0
    compra_red = 0.0
    generacion = 0.0

    for d, fv_unit in zip(demanda_8760_kwh, fv_unitario_8760_kwh_kwp):

        d = float(d or 0.0)
        f = float(fv_unit or 0.0) * kwp

        generacion += f
        autoconsumo += min(d, f)
        excedente += max(f - d, 0.0)
        compra_red += max(d - f, 0.0)

    valor_autoconsumo = autoconsumo * tarifa_compra_l_kwh
    valor_inyeccion = excedente * precio_inyeccion_l_kwh

    demanda_total = sum(demanda_8760_kwh)

    return {
        "kwp": kwp,
        "demanda_kwh_anual": demanda_total,
        "generacion_kwh_anual": generacion,
        "autoconsumo_kwh_anual": autoconsumo,
        "excedente_kwh_anual": excedente,
        "compra_red_kwh_anual": compra_red,
        "valor_autoconsumo_l_anual": valor_autoconsumo,
        "valor_inyeccion_l_anual": valor_inyeccion,
        "beneficio_l_anual": valor_autoconsumo + valor_inyeccion,
        "cobertura_directa_pct": autoconsumo / demanda_total * 100 if demanda_total > 0 else 0.0,
        "excedente_pct_generacion": excedente / generacion * 100 if generacion > 0 else 0.0,
    }


def optimizar_kwp_maximo_ahorro(
    *,
    demanda_24h: Dict[int, float],
    energia_horaria_base_kwh: List[float],
    pdc_kw_base: float,
    panel_w: float,
    tarifa_compra_l_kwh: float,
    precio_inyeccion_l_kwh: float = 2.20,
    kwp_min: float = 1.0,
    kwp_max: float = 500.0,
    paso_kwp: float = 1.0,
    mejora_minima_l_anual: float = 1000.0,
) -> dict:

    demanda_8760 = construir_demanda_8760_desde_24h(
        demanda_24h=demanda_24h,
        n_horas=len(energia_horaria_base_kwh),
    )

    fv_unitario = construir_perfil_unitario_fv_8760(
        energia_horaria_kwh=energia_horaria_base_kwh,
        pdc_kw_base=pdc_kw_base,
    )

    mejor = None
    anterior = None

    kwp = float(kwp_min)

    while kwp <= kwp_max:

        r = evaluar_balance_8760(
            demanda_8760_kwh=demanda_8760,
            fv_unitario_8760_kwh_kwp=fv_unitario,
            kwp=kwp,
            tarifa_compra_l_kwh=tarifa_compra_l_kwh,
            precio_inyeccion_l_kwh=precio_inyeccion_l_kwh,
        )

        n_paneles = int(ceil((kwp * 1000.0) / panel_w))
        pdc_kw_real = n_paneles * panel_w / 1000.0

        r["n_paneles"] = n_paneles
        r["pdc_kw"] = pdc_kw_real

        if anterior is None:
            r["beneficio_marginal_l_anual"] = r["beneficio_l_anual"]
        else:
            r["beneficio_marginal_l_anual"] = (
                r["beneficio_l_anual"] - anterior["beneficio_l_anual"]
            )

        if mejor is None or r["beneficio_l_anual"] > mejor["beneficio_l_anual"]:
            mejor = r

        if anterior is not None and r["beneficio_marginal_l_anual"] < mejora_minima_l_anual:
            break

        anterior = r
        kwp += paso_kwp

    if mejor is None:
        raise ValueError("No se pudo optimizar el sistema FV")

    return mejor
