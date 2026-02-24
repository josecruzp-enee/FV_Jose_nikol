# electrical/strings.py  (legacy)
from __future__ import annotations

from typing import Any, Dict, List

from electrical.paneles.orquestador_paneles import ejecutar_calculo_strings, a_lineas_strings


def calcular_strings_dc(
    *,
    n_paneles: int,
    panel: Any,
    inversor: Any,
    dos_aguas: bool,
    t_min_c: float = 10.0,
    t_ref_c: float = 25.0,  # mantenido por compat; ya no se usa
    min_modulos_serie: int = 6,  # mantenido por compat; el motor decide bounds reales
) -> Dict[str, Any]:
    # Compat: mapeamos n_paneles -> n_paneles_total
    return ejecutar_calculo_strings(
        n_paneles_total=int(n_paneles),
        panel=panel,
        inversor=inversor,
        dos_aguas=bool(dos_aguas),
        t_min_c=float(t_min_c),
    )


def a_lineas(cfg: Dict[str, Any]) -> List[str]:
    return a_lineas_strings(cfg)
