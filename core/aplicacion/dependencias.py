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
from core.dominio.contrato import ResultadoStrings, StringInfo


class PanelesAdapter:

    def ejecutar(self, datos, sizing):

        eq = getattr(datos, "equipos", {}) or {}
        sf = getattr(datos, "sistema_fv", {}) or {}

        panel_id = eq.get("panel_id")
        inversor_id = eq.get("inversor_id")

        panel = get_panel(panel_id)
        inversor = get_inversor(inversor_id)

        # ------------------------------------------------------
        # MODO DE DIMENSIONADO
        # ------------------------------------------------------

        modo = sf.get("modo_dimensionado", "auto")

        if modo == "manual":
            n_paneles_total = sizing.n_paneles
            pdc_kw_objetivo = None
        else:
            n_paneles_total = None
            pdc_kw_objetivo = sizing.pdc_kw

        # ------------------------------------------------------
        # CONSTRUIR ENTRADA DEL DOMINIO
        # ------------------------------------------------------

        entrada = EntradaPaneles(
            panel=panel,
            inversor=inversor,
            n_paneles_total=n_paneles_total,
            n_inversores=sizing.n_inversores,
            t_min_c=sf.get("t_min_c", 10),
            t_oper_c=sf.get("t_oper_c", 45),
            dos_aguas=sf.get("dos_aguas", False),
            objetivo_dc_ac=sf.get("dc_ac_ratio", 1.2),
            pdc_kw_objetivo=pdc_kw_objetivo,
        )

        res = ejecutar_paneles(entrada)

        # ------------------------------------------------------
        # ADAPTAR DICT → ResultadoStrings
        # ------------------------------------------------------

        if not res.get("ok", False):
            raise ValueError(f"Error en dominio paneles: {res.get('errores')}")

        strings_raw = res.get("strings", [])
        strings = []

        for s in strings_raw:
            strings.append(
                StringInfo(
                    id=s["id"],
                    inversor=s["inversor"],
                    mppt=s["mppt"],
                    n_series=s["n_series"],
                    vmp_string_v=s["vmp_string_v"],
                    voc_frio_string_v=s["voc_frio_string_v"],
                    imp_string_a=s["imp_string_a"],
                    isc_string_a=s["isc_string_a"],
                )
            )

        rec = res.get("recomendacion", {})

        return ResultadoStrings(
            ok=True,
            n_series=rec.get("n_series", 0),
            n_strings_total=rec.get("n_strings_total", len(strings)),
            vmp_string_v=rec.get("vmp_string_v", 0),
            voc_string_v=rec.get("voc_string_v", 0),
            strings=strings,
        )




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
