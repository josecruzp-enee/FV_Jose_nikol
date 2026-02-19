# nucleo/simulacion_12m.py
from __future__ import annotations

from typing import Dict, List
import math

from .modelo import Datosproyecto


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


# =========================
# NUEVO: ajuste por orientación (azimut)
# =========================
def _delta_azimut_deg(az_deg: float, ref_deg: float = 180.0) -> float:
    """Distancia angular mínima (0..180). Ref=180 (Sur) para Honduras (hemisferio norte)."""
    d = abs(float(az_deg) - float(ref_deg)) % 360.0
    return min(d, 360.0 - d)


def _factor_orientacion(az_deg: float) -> float:
    """
    Factor simple y estable:
      f = (1 + cos(delta)) / 2
    Sur (180) => 1.0
    Este/Oeste (90/270) => 0.5
    Norte (0) => 0.0 (pero ponemos piso)
    """
    delta = _delta_azimut_deg(az_deg, 180.0)
    f = (1.0 + math.cos(math.radians(delta))) / 2.0
    return max(0.20, min(1.00, f))  # piso 0.20 para no colapsar casos raros


def _factor_orientacion_total(p: Datosproyecto) -> float:
    """
    Usa p.tipo_superficie si existe; si no, intenta p.params_fv["tipo_superficie"].
    - plano: usa azimut_deg
    - dos_aguas: pondera A/B por reparto_pct_a
    """
    tipo = getattr(p, "tipo_superficie", None)
    if not tipo:
        params = getattr(p, "params_fv", None) or {}
        if isinstance(params, dict):
            tipo = params.get("tipo_superficie", None)

    tipo = str(tipo or "plano").lower()

    if tipo != "dos_aguas":
        az = getattr(p, "azimut_deg", None)
        if az is None:
            params = getattr(p, "params_fv", None) or {}
            az = params.get("azimut_deg", 180.0) if isinstance(params, dict) else 180.0
        return _factor_orientacion(float(az))

    # dos aguas
    az_a = getattr(p, "azimut_a_deg", None)
    az_b = getattr(p, "azimut_b_deg", None)
    rep_a = getattr(p, "reparto_pct_a", None)

    if az_a is None or az_b is None or rep_a is None:
        params = getattr(p, "params_fv", None) or {}
        if isinstance(params, dict):
            az_a = params.get("azimut_a_deg", 180.0)
            az_b = params.get("azimut_b_deg", 0.0)
            rep_a = params.get("reparto_pct_a", 50.0)
        else:
            az_a, az_b, rep_a = 180.0, 0.0, 50.0

    w_a = max(0.0, min(1.0, float(rep_a) / 100.0))
    w_b = 1.0 - w_a

    return w_a * _factor_orientacion(float(az_a)) + w_b * _factor_orientacion(float(az_b))


def simular_12_meses(p: Datosproyecto, kwp: float, cuota_mensual_: float, capex_L_: float) -> List[Dict[str, float]]:
    tabla: List[Dict[str, float]] = []
    om_ = om_mensual(capex_L_, p.om_anual_pct)

    # ✅ NUEVO: factor de orientación (constante para el año en este modelo)
    f_orient = _factor_orientacion_total(p)

    for i in range(12):
        consumo = float(p.consumo_12m[i])
        factor = float(p.factores_fv_12m[i])

        # ✅ NUEVO: aplicar orientación aquí
        gb = gen_bruta_mes(kwp, p.prod_base_kwh_kwp_mes, factor) * f_orient
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
