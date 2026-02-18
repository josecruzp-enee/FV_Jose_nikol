# electrical/catalogos.py
from __future__ import annotations
from electrical.modelos import Panel, Inversor

PANELES = {
    "Genérico 550W": Panel("Genérico 550W", w=550, vmp=41.0, voc=50.0, imp=13.0, isc=13.8),
    "Mono 610W":     Panel("Mono 610W",     w=610, vmp=42.2, voc=51.3, imp=14.5, isc=15.2),
}

INVERSORES = {
    "10 kW 1F 240V (2 MPPT)": Inversor("10 kW 1F 240V (2 MPPT)", kw_ac=10.0, n_mppt=2, vmppt_min=200, vmppt_max=800, vdc_max=1000),
    "8 kW 1F 240V (2 MPPT)":  Inversor("8 kW 1F 240V (2 MPPT)",  kw_ac=8.0,  n_mppt=2, vmppt_min=200, vmppt_max=800, vdc_max=1000),
}
