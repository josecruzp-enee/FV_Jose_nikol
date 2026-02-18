# nucleo/simulacion_12m.py
from __future__ import annotations

from typing import Dict, List

from core.modelo import modelo


def consumo_anual(consumo_12m: List[float]) -> float:
    return float(sum(consumo_12m))


def consumo_promedio(consumo_12m: List[float]) -> float:
    return consumo_anual(consumo_12m) / 12.0


def capex_L(kwp: float, costo_usd_kwp: float, tcambio: float) -> float:
    return float(kwp) * float(costo_usd_kwp) * float(tcambio)


def calcular_cuota_mensual(capex_L_: float, tasa_anual: float, plazo_anios: int, pct_fin: float) -> float:
    principal = float(capex_L_) * float(pct_fin)
    r = float(tasa_anual) / 12.0
    n = int(plazo_anios) * 12
    if abs(r) < 1e-12:
        return principal / n
    return (r * principal) / (1 - (1 + r) ** (-n))


def om_mensual(capex_L_: float, om_anual_pct: float) -> float:
    return (float(om_anual_pct) * float(capex_L_)) / 12.0


def gen_bruta_mes(kwp: float, prod_base_kwh_kwp_mes: float, factor: float) -> float:
    return float(kwp) * float(prod_base_kwh_kwp_mes) * float(factor)


def gen_util_mes(consumo_kwh: float, gen_bruta_kwh: float) -> float:
    return min(float(consumo_kwh), float(gen_bruta_kwh))  # sin exportación


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


def simular_12_meses(p: DatosProyecto, kwp: float, cuota_mensual_: float, capex_L_: float) -> List[Dict[str, float]]:
    tabla: List[Dict[str, float]] = []
    om_ = om_mensual(capex_L_, p.om_anual_pct)

    for i in range(12):
        consumo = float(p.consumo_12m[i])
        factor = float(p.factores_fv_12m[i])

        gb = gen_bruta_mes(kwp, p.prod_base_kwh_kwp_mes, factor)
        gu = gen_util_mes(consumo, gb)
        ke = kwh_enee_mes(consumo, gu)

        fb = factura_base_mes(consumo, p.tarifa_energia, p.cargos_fijos)
        pe = pago_enee_mes(ke, p.tarifa_energia, p.cargos_fijos)

        ah = ahorro_mes(fb, pe)
        nt = neto_mes(ah, cuota_mensual_, om_)

        tabla.append({
            "mes": i + 1,
            "consumo_kwh": consumo,
            "fv_kwh": gu,
            "kwh_enee": ke,
            "tarifa_L_kwh": float(p.tarifa_energia),
            "factura_base_L": fb,
            "pago_enee_L": pe,
            "ahorro_L": ah,
            "cuota_L": float(cuota_mensual_),
            "om_L": float(om_),
            "neto_L": nt,
        })

    return tabla

