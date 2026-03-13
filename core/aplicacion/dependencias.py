from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

from core.servicios.sizing import calcular_sizing_unificado
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.energia.orquestador_energia import ejecutar_motor_energia
from electrical.nec.orquestador_nec import ejecutar_nec
from core.servicios.finanzas import ejecutar_finanzas

from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos import get_panel, get_inversor

from core.dominio.contrato import ResultadoStrings


class NECAdapter:

    def ejecutar(self, datos, sizing, strings):

        # --------------------------------------------------
        # VALIDACIÓN DE CONTRATO
        # --------------------------------------------------

        if not isinstance(strings, ResultadoStrings):
            raise ValueError(
                f"strings no cumple contrato ResultadoStrings: {type(strings)}"
            )

        if strings.n_strings_total <= 0:
            raise ValueError("ResultadoStrings no contiene strings válidos")

        if not strings.strings:
            raise ValueError("Lista de strings vacía")

        # --------------------------------------------------
        # PARÁMETROS DEL SISTEMA
        # --------------------------------------------------

        sf = getattr(datos, "sistema_fv", {}) or {}

        vac_ll = sf.get("vac", 240)
        fases = sf.get("fases", 1)
        fp = sf.get("fp", 1.0)

        vdc_nom = sf.get("vdc_nom", 600)

        # --------------------------------------------------
        # DATOS DEL STRING (primer string representativo)
        # --------------------------------------------------

        s0 = strings.strings[0]

        imp_string = s0.imp_string_a
        isc_string = s0.isc_string_a

        n_strings_total = strings.n_strings_total

        # --------------------------------------------------
        # CONSTRUCCIÓN ENTRADA NEC
        # --------------------------------------------------

        entrada_nec = {

            "electrico": {
                "vac_ll": vac_ll,
                "vac_ln": None,
                "fases": fases,
                "fp": fp,
            },

            "potencia_dc_kw": sizing.pdc_kw,
            "potencia_ac_kw": sizing.kw_ac,

            "vdc_nom": vdc_nom,

            "strings": {
                "imp_string_a": imp_string,
                "isc_string_a": isc_string,
                "strings_por_mppt": 1,
                "n_strings_total": n_strings_total,
            },

            "inversor": {
                "kw_ac": sizing.kw_ac,
                "v_ac_nom_v": vac_ll,
                "fases": fases,
                "fp": fp,
            },
        }

        # --------------------------------------------------
        # EJECUTAR MOTOR NEC
        # --------------------------------------------------

        return ejecutar_nec(entrada_nec, sizing, strings)
