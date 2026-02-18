# electrical/verificacion.py
from __future__ import annotations

from typing import List

from electrical.modelos import ResultadoStrings, SeleccionConductor, ResultadoProtecciones


def verificar(strings: ResultadoStrings,
              cond_dc: SeleccionConductor,
              cond_ac: SeleccionConductor,
              prot: ResultadoProtecciones,
              cfg: dict) -> List[str]:
    adv: List[str] = []

    if not strings.dentro_mppt:
        adv.append("String fuera de ventana MPPT del inversor (revisar serie/paralelo).")

    # Caídas
    objetivo = float(cfg.get("caida_tension_objetivo_pct", 2.0))
    if cond_dc.caida_tension_pct > objetivo:
        adv.append(f"Caída DC alta: {cond_dc.caida_tension_pct:.2f}% > {objetivo:.2f}%.")

    if cond_ac.caida_tension_pct > objetivo:
        adv.append(f"Caída AC alta: {cond_ac.caida_tension_pct:.2f}% > {objetivo:.2f}%.")

    # Ampacidad vs breaker (simple)
    if prot.breaker_ac_a > cond_ac.ampacidad_a:
        adv.append("Breaker AC mayor que la ampacidad seleccionada (subir calibre o ajustar protección).")

    return adv
