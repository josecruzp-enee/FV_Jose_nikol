from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class EscenarioCobertura:
    cobertura: float
    energia_objetivo_kwh: float
    potencia_fv_kw: float
    paneles: int
    produccion_anual_kwh: float
    inversion: float
    ahorro_anual: float
    roi: float
    payback: float


def analizar_cobertura(
    consumo_anual_kwh: float,
    potencia_panel_kw: float,
    energia_1kwp_anual: float,
) -> List[EscenarioCobertura]:

    coberturas = [
        0.10,0.20,0.30,0.40,0.50,
        0.60,0.70,0.80,0.90,1.00
    ]

    resultados: List[EscenarioCobertura] = []

    for c in coberturas:

        energia_objetivo = consumo_anual_kwh * c

        potencia_fv_kw = energia_objetivo / energia_1kwp_anual

        paneles = int(round(potencia_fv_kw / potencia_panel_kw))

        produccion = potencia_fv_kw * energia_1kwp_anual

        # estimaciones financieras simples
        costo_kw = 1200
        tarifa = 5

        inversion = potencia_fv_kw * costo_kw
        ahorro = produccion * tarifa

        roi = ahorro / inversion
        payback = inversion / ahorro

        escenario = EscenarioCobertura(
            cobertura=c,
            energia_objetivo_kwh=energia_objetivo,
            potencia_fv_kw=potencia_fv_kw,
            paneles=paneles,
            produccion_anual_kwh=produccion,
            inversion=inversion,
            ahorro_anual=ahorro,
            roi=roi,
            payback=payback,
        )

        resultados.append(escenario)

    return resultados
