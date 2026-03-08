from core.servicios.sizing import calcular_sizing_unificado
from core.servicios.finanzas import ejecutar_finanzas

from electrical.paneles.orquestador_paneles import ejecutar_paneles_desde_sizing
from electrical.energia.orquestador_energia import ejecutar_motor_energia
from electrical.energia.contrato import EnergiaInput
from electrical.nec.orquestador_nec import ejecutar_nec
from electrical.energia.irradiancia import hsp_12m_base
from .puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
    PuertoFinanzas,
)

from .orquestador_estudio import DependenciasEstudio


# ==========================================================
# ADAPTADORES
# ==========================================================

class SizingAdapter(PuertoSizing):
    def ejecutar(self, datos):
        # Devuelve ResultadoSizing (dataclass fuerte)
        return calcular_sizing_unificado(datos)


class PanelesAdapter(PuertoPaneles):
    def ejecutar(self, datos, sizing):
        # sizing es ResultadoSizing (dataclass)
        return ejecutar_paneles_desde_sizing(datos, sizing)


class EnergiaAdapter(PuertoEnergia):
    def ejecutar(self, datos, sizing, strings):

        # sizing es ResultadoSizing
        pdc_instalada_kw = sizing.pdc_kw
        pac_nominal_kw = sizing.pac_kw

        # Irradiancia mensual obligatoria
        hsp_12m = hsp_12m_base()
        if not hsp_12m:
            raise ValueError(
                "No se encontraron factores mensuales (HSP) en Datosproyecto."
            )

        # Días estándar por mes
        dias_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        # Parámetros físicos desde sistema_fv
        sf = getattr(datos, "sistema_fv", {}) or {}

        inp = EnergiaInput(
            pdc_instalada_kw=pdc_instalada_kw,
            pac_nominal_kw=pac_nominal_kw,
            hsp_12m=hsp_12m,
            dias_mes=dias_mes,
            factor_orientacion=sf.get("factor_orientacion", 1.0),
            perdidas_dc_pct=sf.get("perdidas_dc_pct", 3.0),
            perdidas_ac_pct=sf.get("perdidas_ac_pct", 2.0),
            sombras_pct=sf.get("sombras_pct", 0.0),
            permitir_curtailment=sf.get("permitir_curtailment", True),
        )

        # Devuelve EnergiaResultado (dataclass fuerte)
        return ejecutar_motor_energia(inp)


class NECAdapter(PuertoNEC):

    def ejecutar(self, datos, sizing, strings):

        sf = getattr(datos, "sistema_fv", {}) or {}

        vdc_nom = sf.get("vdc_nom", 600)
        vac_ll = sf.get("vac_ll", 480)
        vac_ln = sf.get("vac_ln", None)
        fases = sf.get("fases", 3)
        fp = sf.get("fp", 1.0)

        strings_list = strings.get("strings", [])

        if strings_list:

            s0 = strings_list[0]

            imp_string = s0.get("imp_a", 0)
            isc_string = s0.get("isc_a", 0)
            strings_por_mppt = s0.get("n_paralelo", 1)

        else:

            imp_string = 0
            isc_string = 0
            strings_por_mppt = 1

        n_strings_total = strings.get("recomendacion", {}).get(
            "n_strings_total", 0
        )

        entrada_nec = {

            "potencia_dc_kw": sizing.pdc_kw,
            "potencia_ac_kw": sizing.pac_kw,

            "vdc_nom": vdc_nom,
            "vac_ll": vac_ll,
            "vac_ln": vac_ln,

            "fases": fases,
            "fp": fp,

            "strings": {
                "imp_string_a": imp_string,
                "isc_string_a": isc_string,
                "strings_por_mppt": strings_por_mppt,
                "n_strings_total": n_strings_total,
            },

            "inversor": {
                "kw_ac": sizing.pac_kw,
                "v_ac_nom_v": vac_ll,
                "fases": fases,
                "fp": fp,
            },
        }

        return ejecutar_nec(entrada_nec, sizing, strings)


class FinanzasAdapter(PuertoFinanzas):
    def ejecutar(self, datos, sizing, energia):
        # Devuelve ResultadoFinanciero (dataclass fuerte)
        return ejecutar_finanzas(
            datos=datos,
            sizing=sizing,
            energia=energia,
        )


# ==========================================================
# FACTORY
# ==========================================================

def construir_dependencias() -> DependenciasEstudio:
    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=NECAdapter(),
        finanzas=FinanzasAdapter(),
    )
