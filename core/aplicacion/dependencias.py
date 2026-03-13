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


# ==========================================================
# ADAPTER SIZING
# ==========================================================

class SizingAdapter:

    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


# ==========================================================
# ADAPTER PANELES
# ==========================================================

class PanelesAdapter:

    def ejecutar(self, datos, sizing):

        eq = getattr(datos, "equipos", {}) or {}

        panel_id = eq.get("panel_id")
        inversor_id = eq.get("inversor_id")

        panel = get_panel(panel_id)
        inversor = get_inversor(inversor_id)

        entrada = EntradaPaneles(

            panel=panel,

            inversor=inversor,

            n_paneles_total=sizing.n_paneles,

            n_inversores=sizing.n_inversores,

            t_min_c=datos.sistema_fv.get("t_min_c", 10),

            t_oper_c=datos.sistema_fv.get("t_oper_c", 45),

            dos_aguas=datos.sistema_fv.get("dos_aguas", False),

            objetivo_dc_ac=datos.sistema_fv.get("dc_ac_ratio", 1.2),

            pdc_kw_objetivo=sizing.pdc_kw

        )

        return ejecutar_paneles(entrada)


# ==========================================================
# ADAPTER ENERGIA
# ==========================================================

class EnergiaAdapter:

    def ejecutar(self, datos, sizing, strings):
        return ejecutar_motor_energia(datos, sizing, strings)


# ==========================================================
# ADAPTER NEC
# ==========================================================

class NECAdapter:

    def ejecutar(self, datos, sizing, strings):

        if not isinstance(strings, ResultadoStrings):
            raise ValueError(
                f"strings no cumple contrato ResultadoStrings: {type(strings)}"
            )

        if strings.n_strings_total <= 0:
            raise ValueError("ResultadoStrings no contiene strings válidos")

        if not strings.strings:
            raise ValueError("Lista de strings vacía")

        sf = getattr(datos, "sistema_fv", {}) or {}

        vac_ll = sf.get("vac", 240)
        fases = sf.get("fases", 1)
        fp = sf.get("fp", 1.0)

        vdc_nom = sf.get("vdc_nom", 600)

        s0 = strings.strings[0]

        imp_string = s0.imp_string_a
        isc_string = s0.isc_string_a

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
                "n_strings_total": strings.n_strings_total,
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
# ADAPTER FINANZAS
# ==========================================================

class FinanzasAdapter:

    def ejecutar(self, datos, sizing, energia):
        return ejecutar_finanzas(datos, sizing, energia)


# ==========================================================
# FACTORY DEPENDENCIAS
# ==========================================================

def construir_dependencias():

    return DependenciasEstudio(

        sizing=SizingAdapter(),

        paneles=PanelesAdapter(),

        energia=EnergiaAdapter(),

        nec=NECAdapter(),

        finanzas=FinanzasAdapter(),

    )
