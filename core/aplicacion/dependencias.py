from __future__ import annotations

"""
CONSTRUCTOR DE DEPENDENCIAS — FV ENGINE

Este módulo construye los adaptadores utilizados por el
orquestador del estudio FV.

El objetivo es desacoplar el motor del sistema de las
implementaciones concretas de cada dominio.
"""

# ==========================================================
# PUERTOS DEL SISTEMA
# ==========================================================

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
    PuertoFinanzas,
)

# ==========================================================
# IMPLEMENTACIONES CONCRETAS
# ==========================================================

from core.servicios.sizing import calcular_sizing_unificado

from electrical.paneles.orquestador_paneles import ejecutar_paneles

from electrical.nec.orquestador_nec import ejecutar_nec

from electrical.energia.orquestador_energia import ejecutar_motor_energia

from core.servicios.finanzas import ejecutar_finanzas


# ==========================================================
# ADAPTADOR NEC
# ==========================================================

class NECAdapter(PuertoNEC):

    def ejecutar(self, datos, sizing, strings):

        sf = getattr(datos, "sistema_fv", {}) or {}

        vdc_nom = sf.get("vdc_nom", 600)
        vac_ll = sf.get("vac_ll", 480)
        vac_ln = sf.get("vac_ln", None)
        fases = sf.get("fases", 3)
        fp = sf.get("fp", 1.0)

        # --------------------------------------------------
        # EXTRAER STRINGS
        # --------------------------------------------------

        strings_list = getattr(strings, "strings", [])

        if strings_list:

            s0 = strings_list[0]

            imp_string = getattr(s0, "imp_string_a", 0)
            isc_string = getattr(s0, "isc_string_a", 0)
            strings_por_mppt = 1

        else:

            imp_string = 0
            isc_string = 0
            strings_por_mppt = 1

        n_strings_total = getattr(strings, "n_strings_total", 0)

        # --------------------------------------------------
        # ENTRADA NEC
        # --------------------------------------------------

        entrada_nec = {

            "electrico": {
                "vac_ll": vac_ll,
                "vac_ln": vac_ln,
                "fases": fases,
                "fp": fp,
            },

            "potencia_dc_kw": sizing.pdc_kw,
            "potencia_ac_kw": sizing.kw_ac,

            "vdc_nom": vdc_nom,

            "strings": {
                "imp_string_a": imp_string,
                "isc_string_a": isc_string,
                "strings_por_mppt": strings_por_mppt,
                "n_strings_total": n_strings_total,
            },

            "inversor": {
                "kw_ac": sizing.kw_ac,
                "v_ac_nom_v": vac_ll,
                "fases": fases,
                "fp": fp,
            },
        }

        return ejecutar_nec(entrada_nec, sizing, strings)


# ==========================================================
# ADAPTADORES SIMPLES
# ==========================================================

class SizingAdapter(PuertoSizing):

    def ejecutar(self, datos):

        return calcular_sizing_unificado(datos)


class PanelesAdapter(PuertoPaneles):

    def ejecutar(self, datos, sizing):

        return ejecutar_paneles(datos, sizing)


class EnergiaAdapter(PuertoEnergia):

    def ejecutar(self, datos, sizing, strings):

        return ejecutar_motor_energia(datos, sizing, strings)


class FinanzasAdapter(PuertoFinanzas):

    def ejecutar(self, datos, sizing, energia):

        return ejecutar_finanzas(datos, sizing, energia)


# ==========================================================
# CONSTRUCTOR DE DEPENDENCIAS
# ==========================================================

def construir_dependencias():

    """
    Construye todos los adaptadores utilizados por el
    orquestador del estudio FV.
    """

    return {

        "sizing": SizingAdapter(),

        "paneles": PanelesAdapter(),

        "nec": NECAdapter(),

        "energia": EnergiaAdapter(),

        "finanzas": FinanzasAdapter(),

    }
