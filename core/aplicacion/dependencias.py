from core.aplicacion.orquestador_estudio import DependenciasEstudio

from core.dominio.contrato import StringInfo
from core.dominio.contrato import ResultadoStrings
from energy.clima.lector_pvgis import (descargar_clima_pvgis, EntradaClimaPVGIS)

from electrical.catalogos.catalogos import get_panel

from core.servicios.sizing import calcular_sizing_unificado

from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.nec.orquestador_nec import ejecutar_nec

from electrical.catalogos.catalogos import get_panel
from electrical.catalogos.catalogos import get_inversor

from energy.orquestador_energia import ejecutar_motor_energia
from energy.contrato import EnergiaInput

from core.servicios.finanzas import ejecutar_finanzas
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
        sf = getattr(datos, "sistema_fv", {}) or {}

        panel_id = eq.get("panel_id")
        inversor_id = eq.get("inversor_id")

        panel = get_panel(panel_id)
        inversor = get_inversor(inversor_id)

        # --------------------------------------------------
        # MODO DE DIMENSIONADO (UI Streamlit)
        # --------------------------------------------------

        modo = sf.get("modo_dimensionado")

        n_paneles_total = sizing.n_paneles
        pdc_kw_objetivo = None

        # --------------------------------------------------
        # DEBUG
        # --------------------------------------------------

        print("\nDEBUG PANELES ADAPTER")
        print("modo_dimensionado:", modo)
        print("n_paneles_total:", n_paneles_total)
        print("pdc_kw_objetivo:", pdc_kw_objetivo)

        # --------------------------------------------------
        # CONSTRUIR ENTRADA DEL DOMINIO PANELES
        # --------------------------------------------------

        entrada = EntradaPaneles(

            panel=panel,
            inversor=inversor,

            n_paneles_total=n_paneles_total,
            n_inversores=sizing.n_inversores,

            t_min_c=sf.get("t_min_c", 10),
            t_oper_c=sf.get("t_oper_c", 45),

            dos_aguas=sf.get("dos_aguas", False),
            objetivo_dc_ac=sf.get("dc_ac_ratio", 1.2),

            pdc_kw_objetivo=pdc_kw_objetivo
        )

        # --------------------------------------------------
        # EJECUTAR DOMINIO PANELES
        # --------------------------------------------------

        res = ejecutar_paneles(entrada)

        if not res.get("ok", False):
            raise ValueError(f"Error en dominio paneles: {res.get('errores')}")

        # --------------------------------------------------
        # ADAPTAR dict → ResultadoStrings
        # --------------------------------------------------

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

            n_strings_total=rec.get(
                "n_strings_total",
                len(strings)
            ),

            vmp_string_v=rec.get("vmp_string_v", 0),

            voc_string_v=rec.get("voc_string_v", 0),

            strings=strings,
        )


# ==========================================================
# ADAPTER ENERGIA
# ==========================================================

class EnergiaAdapter:

    def ejecutar(self, datos, sizing, strings):

        sf = getattr(datos, "sistema_fv", {}) or {}
        eq = getattr(datos, "equipos", {}) or {}

        # --------------------------------------------------
        # MODO DE SIMULACIÓN
        # --------------------------------------------------

        modo = sf.get("modo_simulacion", "8760")

        # --------------------------------------------------
        # PANEL (OBLIGATORIO PARA 8760)
        # --------------------------------------------------

        panel_id = eq.get("panel_id")
        panel = get_panel(panel_id)

        # --------------------------------------------------
        # CLIMA PVGIS (8760)
        # --------------------------------------------------

        clima = descargar_clima_pvgis(
            EntradaClimaPVGIS(
                lat=sf.get("latitud"),
                lon=sf.get("longitud"),
                startyear=2019,
                endyear=2019
            )
        )

        # --------------------------------------------------
        # CONSTRUIR ENTRADA
        # --------------------------------------------------

        entrada = EnergiaInput(

            # -------------------------------
            # POTENCIA
            # -------------------------------

            pdc_instalada_kw=sizing.pdc_kw,
            pac_nominal_kw=sizing.kw_ac,

            # -------------------------------
            # MODO
            # -------------------------------

            modo_simulacion=modo,

            # -------------------------------
            # HSP
            # -------------------------------

            hsp_12m=sf.get("hsp_12m", [5.5]*12),
            dias_mes=[31,28,31,30,31,30,31,31,30,31,30,31],

            # -------------------------------
            # 8760 (CLAVE)
            # -------------------------------

            clima=clima,
            tilt_deg=sf.get("inclinacion_deg"),  # ← CORREGIDO

            paneles_por_string=getattr(strings, "n_series", None),
            n_strings_total=getattr(strings, "n_strings_total", None),

            pmax_stc_w=panel.pmax_stc_w,
            vmp_stc_v=panel.vmp_stc_v,
            voc_stc_v=panel.voc_stc_v,

            coef_pmax_pct_per_c=getattr(panel, "coef_pmax_pct_per_c", None),
            coef_voc_pct_per_c=getattr(panel, "coef_voc_pct_per_c", None),
            coef_vmp_pct_per_c=getattr(panel, "coef_vmp_pct_per_c", None),

            # -------------------------------
            # PÉRDIDAS
            # -------------------------------

            perdidas_dc_pct=sf.get("perdidas_dc_pct", 0.03),
            perdidas_ac_pct=sf.get("perdidas_ac_pct", 0.02),
            sombras_pct=sf.get("sombras_pct", 0.0),

            # -------------------------------
            # INVERSOR
            # -------------------------------

            eficiencia_inversor=sf.get("eficiencia_inversor", 0.97),
            permitir_clipping=True,

            # -------------------------------
            # UBICACIÓN
            # -------------------------------

            latitud=sf.get("latitud"),
            longitud=sf.get("longitud"),
        )

        # --------------------------------------------------
        # DEBUG
        # --------------------------------------------------

        print("\nDEBUG ENERGIA ADAPTER")
        print("modo_simulacion:", modo)
        print("clima horas:", len(entrada.clima.horas))
        print("tilt:", entrada.tilt_deg)
        print("panel Pmax:", entrada.pmax_stc_w)

        # --------------------------------------------------
        # EJECUTAR MOTOR
        # --------------------------------------------------

        return ejecutar_motor_energia(entrada)


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

        return ejecutar_finanzas(
            datos=datos,
            sizing=sizing,
            energia=energia,
        )


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
