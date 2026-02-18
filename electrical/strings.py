from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import math

@dataclass(frozen=True)
class ModuloFV:
    nombre: str = "Genérico 550W"
    vmp: float = 41.0
    voc: float = 50.0
    imp: float = 13.0
    isc: float = 13.8

def split_parejo(n: int) -> tuple[int, int]:
    izq = (n + 1) // 2
    der = n // 2
    return izq, der

def definir_strings(
    n_paneles: int,
    *,
    dos_aguas: bool = True,
    umbral_dos_aguas: int = 6,
    n_mppt: int = 2,
    min_modulos_serie: int = 6,
    modulo: Optional[ModuloFV] = None,
    mppt_vmin: Optional[float] = None,
    mppt_vmax: Optional[float] = None,
) -> Dict[str, Any]:
    n = int(n_paneles)
    if n <= 0:
        raise ValueError("n_paneles debe ser > 0")

    warnings: List[str] = []

    if n < umbral_dos_aguas:
        dos_aguas = False

    if dos_aguas and n_mppt >= 2:
        izq, der = split_parejo(n)
        mppt_plan = [
            {"mppt": 1, "strings": [{"serie": izq, "paralelo": 1}]},
            {"mppt": 2, "strings": [{"serie": der, "paralelo": 1}]},
        ]
        if der < min_modulos_serie:
            warnings.append(
                f"Der={der} módulos en serie < mínimo recomendado ({min_modulos_serie}). "
                "Sugerencia: mover 1–2 módulos Izq→Der o usar 1 sola agua/MPPT según ventana MPPT."
            )
        topologia = "2-aguas"
    else:
        mppt_plan = [{"mppt": 1, "strings": [{"serie": n, "paralelo": 1}]}]
        topologia = "1-agua"
        if n < min_modulos_serie:
            warnings.append(
                f"{n} módulos en serie < mínimo recomendado ({min_modulos_serie}). "
                "Puede quedar Vmp bajo dependiendo del inversor."
            )

    # Validación eléctrica (si hay datos)
    if modulo is not None and (mppt_vmin is not None or mppt_vmax is not None):
        for m in mppt_plan:
            for s in m["strings"]:
                ns = int(s["serie"])
                vmp_string = ns * float(modulo.vmp)
                voc_string = ns * float(modulo.voc)
                s["vmp_est_V"] = round(vmp_string, 1)
                s["voc_est_V"] = round(voc_string, 1)

                if mppt_vmin is not None and vmp_string < mppt_vmin:
                    warnings.append(f"String {ns}S: Vmp≈{vmp_string:.0f}V < MPPT mínimo ({mppt_vmin:.0f}V).")
                if mppt_vmax is not None and voc_string > mppt_vmax:
                    warnings.append(f"String {ns}S: Voc≈{voc_string:.0f}V > límite DC ({mppt_vmax:.0f}V).")

    return {"topologia": topologia, "mppt": mppt_plan, "warnings": warnings}

def texto_config_electrica_pdf(cfg: dict, *, etiqueta_izq="Techo izquierdo", etiqueta_der="Techo derecho") -> str:
    strings = []
    # flatten mppt->strings
    for m in cfg.get("mppt", []):
        mppt = m.get("mppt")
        for s in m.get("strings", []):
            strings.append({"mppt": mppt, **s})

    etiquetas = {1: etiqueta_izq, 2: etiqueta_der}
    lines = ["<b>Configuración eléctrica referencial</b><br/>"]

    for s in strings:
        mppt = s["mppt"]
        nom = etiquetas.get(mppt, f"MPPT {mppt}")
        ns = int(s["serie"])
        np = int(s.get("paralelo", 1))

        topologia = f"{ns} módulos en serie ({ns}S)" if np == 1 else f"{np} strings en paralelo de {ns}S ({ns}S×{np}P)"

        vmp = s.get("vmp_est_V")
        voc = s.get("voc_est_V")
        if vmp is not None and voc is not None:
            lines.append(f"• <b>{nom}</b> — {topologia}: Vmp≈{float(vmp):.0f} V | Voc≈{float(voc):.0f} V.<br/>")
        else:
            lines.append(f"• <b>{nom}</b> — {topologia}.<br/>")

    if cfg.get("warnings"):
        lines.append("<br/><b>Notas</b><br/>")
        for w in cfg["warnings"]:
            lines.append(f"• {w}<br/>")

    return "".join(lines)
