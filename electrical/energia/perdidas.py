# electrical/energia/perdidas.py

from __future__ import annotations


def calcular_pr(perdidas_pct: float, sombras_pct: float) -> float:
    """
    Performance Ratio simplificado.
    """

    pr = (1.0 - float(perdidas_pct) / 100.0) * \
         (1.0 - float(sombras_pct) / 100.0)

    return max(0.10, min(1.00, pr))
