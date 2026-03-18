from __future__ import annotations

from dataclasses import dataclass
from typing import List

from energy.panel_energia.potencia_panel import (
    calcular_potencia_panel,
    PotenciaPanelInput,
)

from energy.panel_energia.modelo_termico import (
    calcular_temperatura_celda,
    ModeloTermicoInput
)


# ==========================================================
# ENTRADA
# ==========================================================

@dataclass(frozen=True)
class SolarHora:
    poa_wm2: float
    temp_amb_c: float


@dataclass(frozen=True)
class Array8760Input:

    estado_solar: List[SolarHora]

    paneles_por_string: int
    strings_totales: int

    pmax_stc_w: float
    vmp_stc_v: float
    voc_stc_v: float

    coef_pmax_pct_per_c: float
    coef_voc_pct_per_c: float
    coef_vmp_pct_per_c: float


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass(frozen=True)
class Array8760Resultado:
    potencia_dc_kw: List[float]


# ==========================================================
# MOTOR
# ==========================================================

def calcular_array_8760(inp: Array8760Input) -> Array8760Resultado:

    if len(inp.estado_solar) == 0:
        raise ValueError("estado_solar vacío")

    if len(inp.estado_solar) not in (8760, 8784):
        raise ValueError("Serie inválida")

    n = len(inp.estado_solar)
    potencia_dc_kw = [0.0] * n

    for i, hora in enumerate(inp.estado_solar):

        if hora.poa_wm2 <= 0:
            continue

        # ---------------------------------------------
        # TEMPERATURA CELDA (AHORA AQUÍ)
        # ---------------------------------------------

        temp = calcular_temperatura_celda(
            ModeloTermicoInput(
                irradiancia_poa_wm2=hora.poa_wm2,
                temperatura_ambiente_c=hora.temp_amb_c,
                noct_c=45
            )
        )

        # ---------------------------------------------
        # PANEL
        # ---------------------------------------------

        panel = calcular_potencia_panel(
            PotenciaPanelInput(
                irradiancia_poa_wm2=hora.poa_wm2,
                temperatura_celda_c=temp.temperatura_celda_c,

                pmax_stc_w=inp.pmax_stc_w,
                vmp_stc_v=inp.vmp_stc_v,
                voc_stc_v=inp.voc_stc_v,

                coef_pmax_pct_per_c=inp.coef_pmax_pct_per_c,
                coef_voc_pct_per_c=inp.coef_voc_pct_per_c,
                coef_vmp_pct_per_c=inp.coef_vmp_pct_per_c,
            )
        )

        potencia_string_w = panel.pmp_w * inp.paneles_por_string
        potencia_array_w = potencia_string_w * inp.strings_totales

        potencia_dc_kw[i] = max(potencia_array_w, 0.0) / 1000.0

    return Array8760Resultado(
        potencia_dc_kw=potencia_dc_kw
    )
