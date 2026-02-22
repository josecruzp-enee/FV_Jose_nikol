# electrical/strings.py
from __future__ import annotations

from typing import Any, Dict, List
from electrical.modelos import Panel, Inversor


def _split_parejo(n: int) -> tuple[int, int]:
    return (n + 1) // 2, n // 2


def calcular_strings_dc(
    *,
    n_paneles: int,
    panel: Panel,
    inversor: Inversor,
    dos_aguas: bool,
    t_min_c: float = 10.0,
    t_ref_c: float = 25.0,
    min_modulos_serie: int = 6,
) -> Dict[str, Any]:
    """
    Calcula strings DC (1 string por MPPT) y validaciones de voltaje.
    Retorna:
      - topologia
      - strings: [{mppt, etiqueta, ns, np, vmp_V, voc_frio_V, imp_A, isc_A}]
      - checks: lista mensajes
      - params
    """
    n = int(n_paneles)
    if n <= 0:
        raise ValueError("n_paneles debe ser > 0")

    checks: List[str] = []

    # Voc frío (Voc sube al bajar temperatura)
    tc_abs = abs(float(panel.tc_voc_frac_c))
    voc_factor_frio = 1.0 + tc_abs * (float(t_ref_c) - float(t_min_c))

    # reparto por MPPT
    if dos_aguas and inversor.n_mppt >= 2 and n >= 6:
        izq, der = _split_parejo(n)
        grupos = [(1, "Techo izquierdo", izq), (2, "Techo derecho", der)]
        topologia = "2-aguas"
    else:
        grupos = [(1, "Arreglo FV", n)]
        topologia = "1-agua"

    out: List[Dict[str, Any]] = []
    for mppt, etiqueta, ns in grupos:
        ns = int(ns)
        np = 1

        if ns < min_modulos_serie:
            checks.append(f"⚠️ {etiqueta}: {ns}S < mínimo recomendado ({min_modulos_serie}).")

        vmp = ns * panel.vmp
        voc_frio = (ns * panel.voc) * voc_factor_frio
        imp = panel.imp * np
        isc = panel.isc * np

        if vmp < inversor.vmppt_min:
            checks.append(f"⚠️ {etiqueta}: Vmp≈{vmp:.0f} V < Vmppt_min={inversor.vmppt_min:.0f} V.")
        if vmp > inversor.vmppt_max:
            checks.append(f"⚠️ {etiqueta}: Vmp≈{vmp:.0f} V > Vmppt_max={inversor.vmppt_max:.0f} V.")
        if voc_frio > inversor.vdc_max:
            checks.append(f"❌ {etiqueta}: Voc frío≈{voc_frio:.0f} V > Vdc_max={inversor.vdc_max:.0f} V.")

        out.append({
            "mppt": mppt,
            "etiqueta": etiqueta,
            "ns": ns,
            "np": np,
            "vmp_V": round(vmp, 1),
            "voc_frio_V": round(voc_frio, 1),
            "imp_A": round(imp, 2),
            "isc_A": round(isc, 2),
        })

    return {
        "topologia": topologia,
        "strings": out,
        "checks": checks,
        "params": {
            "t_min_c": float(t_min_c),
            "voc_factor_frio": round(voc_factor_frio, 4),
        },
    }


def a_lineas(cfg: Dict[str, Any]) -> List[str]:
    """Líneas listas para UI/PDF."""
    lines: List[str] = []
    for s in cfg.get("strings", []):
        lines.append(
            f"{s['etiqueta']} — {s['ns']}S: Vmp≈{s['vmp_V']:.0f} V | Voc frío≈{s['voc_frio_V']:.0f} V | Imp≈{s['imp_A']:.1f} A."
        )
    return lines
