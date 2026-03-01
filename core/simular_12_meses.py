# core/simulacion_12m.py
from __future__ import annotations

from typing import Dict, List
from .modelo import Datosproyecto
from core.finanzas_lp import om_mensual
from electrical.energia.orientacion import factor_orientacion_total


def gen_bruta_mes(kwp: float, prod_base_kwh_kwp_mes: float, factor: float) -> float:
    return float(kwp) * float(prod_base_kwh_kwp_mes) * float(factor)


def gen_util_mes(consumo_kwh: float, gen_bruta_kwh: float) -> float:
    return min(float(consumo_kwh), float(gen_bruta_kwh))


def kwh_enee_mes(consumo_kwh: float, gen_util_kwh: float) -> float:
    return float(consumo_kwh) - float(gen_util_kwh)


def factura_base_mes(consumo_kwh: float, tarifa_L_kwh: float, cargos_fijos_L: float) -> float:
    return float(consumo_kwh) * float(tarifa_L_kwh) + float(cargos_fijos_L)


def pago_enee_mes(kwh_enee: float, tarifa_L_kwh: float, cargos_fijos_L: float) -> float:
    return float(kwh_enee) * float(tarifa_L_kwh) + float(cargos_fijos_L)


def ahorro_mes(factura_base: float, pago_enee: float) -> float:
    return float(factura_base) - float(pago_enee)


def neto_mes(ahorro: float, cuota: float, om: float) -> float:
    return float(ahorro) - float(cuota) - float(om)


def simular_12_meses(
    p: Datosproyecto,
    kwp: float,
    cuota_mensual_: float,
    capex_L_: float,
) -> List[Dict[str, float]]:

    tabla: List[Dict[str, float]] = []

    consumo_12m = list(p.consumo_12m)
    factores_12m = list(p.factores_fv_12m)
    tarifa = float(p.tarifa_energia)
    cargos = float(p.cargos_fijos)
    prod_base = float(p.prod_base_kwh_kwp_mes)

    om_ = om_mensual(capex_L_, p.om_anual_pct)

    f_orient = factor_orientacion_total(
        tipo_superficie=p.tipo_superficie,
        azimut_deg=p.azimut_deg,
        azimut_a_deg=getattr(p, "azimut_a_deg", None),
        azimut_b_deg=getattr(p, "azimut_b_deg", None),
        reparto_pct_a=getattr(p, "reparto_pct_a", None),
    )

    for i in range(12):

        consumo = float(consumo_12m[i])
        factor = float(factores_12m[i])

        gb = gen_bruta_mes(kwp, prod_base, factor) * f_orient
        gu = gen_util_mes(consumo, gb)
        ke = kwh_enee_mes(consumo, gu)

        fb = factura_base_mes(consumo, tarifa, cargos)
        pe = pago_enee_mes(ke, tarifa, cargos)

        ah = ahorro_mes(fb, pe)
        nt = neto_mes(ah, cuota_mensual_, om_)

        tabla.append({
            "mes": i + 1,
            "consumo_kwh": consumo,
            "fv_kwh": gu,
            "kwh_enee": ke,
            "factura_base_L": fb,
            "pago_enee_L": pe,
            "ahorro_L": ah,
            "cuota_L": float(cuota_mensual_),
            "om_L": float(om_),
            "neto_L": nt,
        })

    return tabla
