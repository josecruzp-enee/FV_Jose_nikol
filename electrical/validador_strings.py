# electrical/validador_strings.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


# ==========================================================
# MODELOS
# ==========================================================

@dataclass
class PanelFV:
    voc: float        # Voc STC (V)
    vmp: float        # Vmp (V)
    isc: float        # Isc (A)
    imp: float        # Imp (A)
    coef_voc: float   # coef temperatura (%/°C)


@dataclass
class InversorFV:
    vdc_max: float
    mppt_min: float
    mppt_max: float
    imppt_max: float
    n_mppt: int


# ==========================================================
# CALCULO VOC FRIO
# ==========================================================

def calcular_voc_frio(
    voc_stc: float,
    coef_temp: float,
    temp_min: float = 10.0,
    temp_stc: float = 25.0
) -> float:
    """
    Voc corregido por temperatura fría.
    Honduras típico: 8–12°C madrugadas montaña.
    """
    delta_t = temp_min - temp_stc
    factor = 1 + (coef_temp / 100.0) * delta_t
    return voc_stc * factor


# ==========================================================
# VALIDADOR PRINCIPAL
# ==========================================================

def validar_string(
    panel: PanelFV,
    inversor: InversorFV,
    n_paneles_string: int,
    temp_min: float = 10.0
) -> Dict:

    voc_frio_panel = calcular_voc_frio(
        panel.voc,
        panel.coef_voc,
        temp_min=temp_min
    )

    voc_total = voc_frio_panel * n_paneles_string
    vmp_total = panel.vmp * n_paneles_string
    corriente = panel.imp

    resultado = {
        "voc_frio_total": round(voc_total, 1),
        "vmp_operativo": round(vmp_total, 1),
        "corriente_mppt": corriente,
        "ok_vdc": voc_total < inversor.vdc_max,
        "ok_mppt": inversor.mppt_min <= vmp_total <= inversor.mppt_max,
        "ok_corriente": corriente <= inversor.imppt_max,
    }

    resultado["string_valido"] = all([
        resultado["ok_vdc"],
        resultado["ok_mppt"],
        resultado["ok_corriente"],
    ])

    return resultado
