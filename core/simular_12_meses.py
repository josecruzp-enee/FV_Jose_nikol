# core/simulacion_12m.py
from __future__ import annotations

from typing import Dict, List


def simular_12_meses(
    *,
    consumo_12m: List[float],
    factores_12m: List[float],
    tarifa_energia: float,
    cargos_fijos: float,
    prod_base_kwh_kwp_mes: float,
    kwp: float,
    cuota_mensual: float,
    om_mensual_val: float,
    factor_orientacion: float,
) -> List[Dict[str, float]]:
    """
    Modelo operativo mensual FV.

    No depende de Datosproyecto.
    No depende de finanzas.
    No depende de orientación interna.

    Función pura.
    """

    if len(consumo_12m) != 12:
        raise ValueError("consumo_12m debe tener 12 valores")

    if len(factores_12m) != 12:
        raise ValueError("factores_12m debe tener 12 valores")

    tabla: List[Dict[str, float]] = []

    for i in range(12):

        consumo = float(consumo_12m[i])
        factor = float(factores_12m[i])

        # Generación bruta
        gen_bruta = (
            float(kwp)
            * float(prod_base_kwh_kwp_mes)
            * factor
            * float(factor_orientacion)
        )

        # Generación útil (sin exportación)
        gen_util = min(consumo, gen_bruta)

        # Energía comprada a red
        kwh_enee = consumo - gen_util

        # Facturación
        factura_base = consumo * float(tarifa_energia) + float(cargos_fijos)
        pago_enee = kwh_enee * float(tarifa_energia) + float(cargos_fijos)

        # Ahorro
        ahorro = factura_base - pago_enee

        # Flujo neto
        neto = ahorro - float(cuota_mensual) - float(om_mensual_val)

        tabla.append({
            "mes": i + 1,
            "consumo_kwh": consumo,
            "fv_kwh": gen_util,
            "kwh_enee": kwh_enee,
            "factura_base_L": factura_base,
            "pago_enee_L": pago_enee,
            "ahorro_L": ahorro,
            "cuota_L": float(cuota_mensual),
            "om_L": float(om_mensual_val),
            "neto_L": neto,
        })

    return tabla
