from __future__ import annotations
from dataclasses import dataclass
from math import ceil
from typing import List

from .entrada_panel import EntradaPaneles


@dataclass(frozen=True)
class PanelSizingResultado:
    ok: bool
    errores: List[str]
    kwp_req: float
    n_paneles: int
    pdc_kw: float


def dimensionar_paneles(entrada: EntradaPaneles) -> PanelSizingResultado:

    errores: List[str] = []

    try:
        panel_w = float(entrada.panel.pmax_w)
    except Exception:
        return PanelSizingResultado(False, ["Panel inválido"], 0, 0, 0)

    if entrada.n_paneles_total and entrada.pdc_kw_objetivo:
        return PanelSizingResultado(
            False,
            ["Definir solo uno: n_paneles_total o pdc_kw_objetivo"],
            0, 0, 0
        )

    try:

        if entrada.n_paneles_total is not None:
            n_paneles = int(entrada.n_paneles_total)
            if n_paneles <= 0:
                raise ValueError("n_paneles_total inválido")

            kwp_req = (n_paneles * panel_w) / 1000

        else:
            kwp_req = float(entrada.pdc_kw_objetivo or 0)
            if kwp_req <= 0:
                raise ValueError("pdc_kw_objetivo inválido")

            n_paneles = ceil((kwp_req * 1000) / panel_w)

        pdc_kw = (n_paneles * panel_w) / 1000

        return PanelSizingResultado(True, [], kwp_req, n_paneles, pdc_kw)

    except Exception as e:
        return PanelSizingResultado(False, [str(e)], 0, 0, 0)
