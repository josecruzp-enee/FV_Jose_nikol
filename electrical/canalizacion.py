# electrical/canalizacion.py
from __future__ import annotations
from typing import Dict

def conduit_ac_heuristico(*, awg_ac: str, incluye_neutro: bool, extra_ccc: int = 0) -> str:
    ccc = 2 + (1 if incluye_neutro else 0) + max(0, int(extra_ccc))
    base = '1/2"' if awg_ac in ["14", "12", "10", "8"] else ('3/4"' if awg_ac == "6" else '1"')
    if ccc < 4:
        return base
    return '3/4"' if base == '1/2"' else ('1"' if base == '3/4"' else '1-1/4"')

def tuberia_por_cantidad(n: int) -> str:
    x = int(n)
    if x <= 3:
        return '1/2"'
    if x <= 6:
        return '3/4"'
    if x <= 9:
        return '1"'
    return '1-1/4"'

def canalizacion_tramo(*, n_conductores: int, nota: str) -> Dict[str, str]:
    return {"tuberia": tuberia_por_cantidad(n_conductores), "nota": str(nota)}

def canalizacion_fv(*, tiene_trunk: bool, fases_ac: int, incluye_neutro: bool) -> Dict[str, Dict[str, str]]:
    n_ac = 2 if int(fases_ac) == 1 else 3
    n_ac += (1 if incluye_neutro else 0)
    return {
        "dc_string": canalizacion_tramo(n_conductores=2, nota="2 conductores (±) referencial."),
        "dc_trunk": canalizacion_tramo(n_conductores=2, nota="2 conductores (±) referencial.") if tiene_trunk else {"tuberia": "", "nota": "No aplica."},
        "ac_out": canalizacion_tramo(n_conductores=n_ac, nota="L1/L2(+L3) + (N si aplica) referencial; agregar EGC si aplica."),
    }
