from __future__ import annotations

"""
ADAPTADOR NEC — FV ENGINE

Este módulo actúa como frontera entre:

    Motor FV
        ↓
    Motor NEC

Responsabilidad:
    - leer resultados de sizing y strings
    - construir entrada NEC
    - ejecutar paquete NEC

NO calcula ingeniería eléctrica directamente.
"""

from typing import Dict, Any

from core.dominio.contrato import ResultadoSizing
from electrical.ingenieria_electrica import ejecutar_ingenieria_electrica


# ==========================================================
# UTILIDAD: lista de strings
# ==========================================================

def _lista_strings(strings):

    if not strings:
        return []

    if isinstance(strings, dict):
        return strings.get("strings", [])

    if hasattr(strings, "strings"):
        return strings.strings

    if isinstance(strings, list):
        return strings

    return []


# ==========================================================
# UTILIDAD: leer base eléctrica del proyecto
# ==========================================================

def _leer_base_electrica(p):

    if isinstance(p, dict):
        base = p.get("electrico", {})
    else:
        base = getattr(p, "electrico", {})

    vac_ll = base.get("vac") or base.get("vac_ll")
    fases = base.get("fases", 1)
    fp = base.get("fp", 1.0)

    return vac_ll, fases, fp


# ==========================================================
# EXTRAER DATOS DE STRINGS
# ==========================================================

def _datos_strings(strings):

    lista = _lista_strings(strings)

    if not lista:

        return {
            "n_strings": 0,
            "imp_string_a": 0,
            "isc_string_a": 0,
            "vmp_string_v": 0
        }

    s0 = lista[0]

    if isinstance(s0, dict):

        imp = s0.get("imp_string_a", 0)
        isc = s0.get("isc_string_a", 0)
        vmp = s0.get("vmp_string_v", 0)

    else:

        imp = getattr(s0, "imp_string_a", 0)
        isc = getattr(s0, "isc_string_a", 0)
        vmp = getattr(s0, "vmp_string_v", 0)

    return {
        "n_strings": len(lista),
        "imp_string_a": imp,
        "isc_string_a": isc,
        "vmp_string_v": vmp
    }


# ==========================================================
# CONSTRUIR ENTRADA NEC
# ==========================================================

def _construir_entrada_nec(
    p,
    sizing: ResultadoSizing,
    strings
):

    vac_ll, fases, fp = _leer_base_electrica(p)

    datos_strings = _datos_strings(strings)

    potencia_dc = getattr(sizing, "pdc_kw", 0) * 1000
    potencia_ac = getattr(sizing, "kw_ac", 0) * 1000

    entrada_nec = {

        "n_strings": datos_strings["n_strings"],

        "imp_string_a": datos_strings["imp_string_a"],
        "isc_string_a": datos_strings["isc_string_a"],

        "potencia_dc_w": potencia_dc,
        "potencia_ac_w": potencia_ac,

        "vdc_nom": datos_strings["vmp_string_v"],
        "vac_ll": vac_ll,

        "fases": fases,
        "fp": fp
    }

    return entrada_nec


# ==========================================================
# ORQUESTADOR NEC
# ==========================================================

def ejecutar_nec(
    p,
    sizing: ResultadoSizing,
    strings
) -> Dict[str, Any]:

    entrada_nec = _construir_entrada_nec(
        p,
        sizing,
        strings
    )

    paquete = armar_paquete_nec(entrada_nec)

    resultado = {
        "entrada_nec": entrada_nec,
        "paquete_nec": paquete
    }

    return resultado


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# ejecutar_nec()
#
# Entrada:
#   proyecto
#   ResultadoSizing
#   strings
#
# Salida:
#   dict
#
# Descripción:
#   Adaptador entre el motor FV y el motor NEC.
#
# Consumido por:
#   core.orquestador_estudio
#
# ==========================================================
