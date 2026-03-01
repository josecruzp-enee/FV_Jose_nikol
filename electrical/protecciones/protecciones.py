from __future__ import annotations
from typing import Dict, Optional

TAMANOS_OCPD_STD = [
    15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 110, 125,
    150, 175, 200
]


def siguiente_ocpd(a: float) -> int:
    x = float(a)
    for s in TAMANOS_OCPD_STD:
        if x <= s:
            return int(s)
    return int(TAMANOS_OCPD_STD[-1])


# ==========================================================
# AC Breaker (Salida inversor)
# NEC 690.8 + 210.20(A)
# ==========================================================

def breaker_ac_nec(
    iac_nom_a: float,
    es_carga_continua: bool = True,
    factor_continua: float = 1.25
) -> Dict[str, float | int]:
    
    i_nom = float(iac_nom_a)

    if es_carga_continua:
        i_diseno = i_nom * factor_continua
    else:
        i_diseno = i_nom

    return {
        "i_nom_a": round(i_nom, 3),
        "i_diseno_a": round(i_diseno, 3),
        "tamano_a": siguiente_ocpd(i_diseno),
        "norma": "NEC 690.8 / 210.20(A)"
    }


# ==========================================================
# Fusible de string (DC)
# NEC 690.9
# ==========================================================

def fusible_string_nec(
    *,
    n_strings: int,
    isc_mod_a: float,
    has_combiner: Optional[bool] = None,
    aplicar_factor_continuo: bool = True
) -> Dict[str, float | int | bool | str]:

    ns = int(n_strings)
    requiere = bool(has_combiner) if has_combiner is not None else (ns >= 3)

    if not requiere or ns < 3:
        return {
            "requerido": False,
            "nota": "Sin combiner o <3 strings en paralelo."
        }

    isc = float(isc_mod_a)

    # NEC típico: 1.25 por condiciones + 1.25 continuo
    factor = 1.25
    if aplicar_factor_continuo:
        factor *= 1.25  # total 1.56

    i_min = isc * factor

    return {
        "requerido": True,
        "i_min_a": round(i_min, 3),
        "tamano_a": siguiente_ocpd(i_min),
        "factor_aplicado": round(factor, 3),
        "norma": "NEC 690.9"
    }


# ==========================================================
# Orquestador protecciones
# ==========================================================

def dimensionar_protecciones_fv(
    *,
    iac_nom_a: float,
    n_strings: int,
    isc_mod_a: float,
    has_combiner: Optional[bool] = None
) -> Dict[str, object]:

    return {
        "breaker_ac": breaker_ac_nec(iac_nom_a),
        "fusible_string": fusible_string_nec(
            n_strings=n_strings,
            isc_mod_a=isc_mod_a,
            has_combiner=has_combiner
        ),
    }
