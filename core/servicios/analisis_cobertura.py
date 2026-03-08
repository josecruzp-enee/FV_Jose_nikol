from __future__ import annotations

from dataclasses import dataclass
from typing import List, Callable


# ==========================================================
# DATACLASS RESULTADO DE ESCENARIO
# ==========================================================

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


# ==========================================================
# SERVICIO PRINCIPAL
# ==========================================================

def analizar_cobertura(
    consumo_anual_kwh: float,
    potencia_panel_kw: float,
    produccion_especifica: float,
    ejecutar_pipeline: Callable[[float], dict],
    coberturas: List[float] | None = None,
) -> List[EscenarioCobertura]:

    """
    Analiza distintos escenarios de cobertura energética FV.

    Parámetros
    ----------
    consumo_anual_kwh : float
        Consumo total anual del cliente.

    potencia_panel_kw : float
        Potencia nominal del panel (ej. 0.55 kW).

    produccion_especifica : float
        Producción específica kWh/kW-año (ej. 1450 Honduras).

    ejecutar_pipeline : Callable
        Función que ejecuta tu pipeline completo dado un tamaño FV (kW).

    coberturas : list
        Porcentajes de cobertura a evaluar.

    """

    if coberturas is None:
        coberturas = [
            0.10, 0.20, 0.30, 0.40, 0.50,
            0.60, 0.70, 0.80, 0.90, 1.00
        ]

    resultados: List[EscenarioCobertura] = []

    for c in coberturas:

        energia_objetivo = consumo_anual_kwh * c

        potencia_fv_kw = energia_objetivo / produccion_especifica

        paneles = int(round(potencia_fv_kw / potencia_panel_kw))

        # Ejecutar pipeline existente
        resultado = ejecutar_pipeline(potencia_fv_kw)

        produccion = resultado["energia"]["produccion_anual_kwh"]
        inversion = resultado["financiero"]["capex_total"]
        ahorro = resultado["financiero"]["ahorro_anual"]
        roi = resultado["financiero"]["roi"]
        payback = resultado["financiero"]["payback"]

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
