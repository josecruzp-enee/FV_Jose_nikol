# electrical/strings.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ModuloFV:
    nombre: str = "Genérico 550W"
    vmp: float = 41.0
    voc: float = 50.0
    imp: float = 13.0
    isc: float = 13.8
    tc_voc_frac_c: float = -0.0029  # -0.29%/°C aprox


def _split_parejo(n: int) -> tuple[int, int]:
    izq = (n + 1) // 2
    der = n // 2
    return izq, der


def plan_strings(
    n_paneles: int,
    *,
    dos_aguas: bool = True,
    umbral_dos_aguas: int = 6,
    n_mppt: int = 2,
    min_modulos_serie: int = 6,
    modulo: Optional[ModuloFV] = None,
    vmppt_min: Optional[float] = None,
    vmppt_max: Optional[float] = None,
    vdc_max: Optional[float] = None,
    t_min_c: float = 10.0,
    t_ref_c: float = 25.0,
) -> Dict[str, Any]:
    """
    Retorna dict con:
      - topologia: "1-agua" / "2-aguas"
      - strings: lista [{mppt, etiqueta, ns, np, vmp, voc_stc, voc_frio, imp, isc}]
      - checks: lista de advertencias/errores
    """
    n = int(n_paneles)
    if n <= 0:
        raise ValueError("n_paneles debe ser > 0")

    checks: List[str] = []

    if n < umbral_dos_aguas:
        dos_aguas = False

    # ---- distribución por MPPT
    grupos: List[tuple[int, str, int]] = []
    if dos_aguas and n_mppt >= 2:
        izq, der = _split_parejo(n)
        grupos = [(1, "Techo izquierdo", izq), (2, "Techo derecho", der)]
        topologia = "2-aguas"
    else:
        grupos = [(1, "Arreglo FV", n)]
        topologia = "1-agua"

    if modulo is None:
        modulo = ModuloFV()

    tc_abs = abs(float(modulo.tc_voc_frac_c))
    voc_factor_frio = 1.0 + tc_abs * (float(t_ref_c) - float(t_min_c))

    out_strings: List[Dict[str, Any]] = []

    for mppt, etiqueta, ns in grupos:
        ns = int(ns)
        if ns <= 0:
            continue

        np = 1  # por defecto 1 string por MPPT (simple y profesional)
        if ns < min_modulos_serie:
            checks.append(f"⚠️ {etiqueta}: {ns}S < mínimo recomendado ({min_modulos_serie}).")

        vmp = ns * float(modulo.vmp)
        voc_stc = ns * float(modulo.voc)
        voc_frio = voc_stc * voc_factor_frio
        imp = float(modulo.imp) * np
        isc = float(modulo.isc) * np

        # validaciones ventana MPPT / Vdc max
        if vmppt_min is not None and vmp < float(vmppt_min):
            checks.append(f"⚠️ {etiqueta}: Vmp≈{vmp:.0f} V < Vmppt_min={float(vmppt_min):.0f} V.")
        if vmppt_max is not None and vmp > float(vmppt_max):
            checks.append(f"⚠️ {etiqueta}: Vmp≈{vmp:.0f} V > Vmppt_max={float(vmppt_max):.0f} V.")
        if vdc_max is not None and voc_frio > float(vdc_max):
            checks.append(f"❌ {etiqueta}: Voc_frío≈{voc_frio:.0f} V > Vdc_max={float(vdc_max):.0f} V.")

        out_strings.append({
            "mppt": mppt,
            "etiqueta": etiqueta,
            "ns": ns,
            "np": np,
            "vmp_V": round(vmp, 1),
            "voc_stc_V": round(voc_stc, 1),
            "voc_frio_V": round(voc_frio, 1),
            "imp_A": round(imp, 2),
            "isc_A": round(isc, 2),
        })

    return {
        "topologia": topologia,
        "strings": out_strings,
        "checks": checks,
        "params": {
            "t_min_c": float(t_min_c),
            "voc_factor_frio": round(voc_factor_frio, 4),
            "vmppt_min": vmppt_min,
            "vmppt_max": vmppt_max,
            "vdc_max": vdc_max,
        },
    }


def strings_to_lines(cfg: Dict[str, Any]) -> List[str]:
    """Líneas lista tipo bullets (para PDF y para Streamlit)."""
    lines: List[str] = []
    for s in cfg.get("strings", []):
        etiqueta = s["etiqueta"]
        ns = s["ns"]
        vmp = s["vmp_V"]
        vocf = s["voc_frio_V"]
        imp = s["imp_A"]
        lines.append(
            f"{etiqueta} — {ns} módulos en serie ({ns}S): Vmp≈{vmp:.0f} V | Voc frío≈{vocf:.0f} V | Imp≈{imp:.1f} A."
        )
    return lines


def strings_to_html(cfg: Dict[str, Any]) -> str:
    """HTML simple para box_paragraph."""
    lines = ["<b>Configuración eléctrica referencial</b><br/>"]
    for s in cfg.get("strings", []):
        etiqueta = s["etiqueta"]
        ns = s["ns"]
        vmp = s["vmp_V"]
        vocf = s["voc_frio_V"]
        imp = s["imp_A"]
        lines.append(
            f"• <b>{etiqueta}</b> — {ns}S: Vmp≈{vmp:.0f} V | Voc frío≈{vocf:.0f} V | Imp≈{imp:.1f} A.<br/>"
        )

    checks = cfg.get("checks") or []
    if checks:
        lines.append("<br/><b>Notas</b><br/>")
        for c in checks:
            lines.append(f"• {c}<br/>")

    return "".join(lines)
