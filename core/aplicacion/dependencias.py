from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

from core.dominio.contrato import StringInfo, ResultadoStrings

from core.servicios.sizing import calcular_sizing_unificado
from energy.clima.lector_pvgis import EntradaClimaPVGIS
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.nec.orquestador_nec import ejecutar_nec

from electrical.catalogos.catalogos import get_panel, get_inversor

from energy.orquestador_energia import ejecutar_motor_energia
from energy.contrato import EnergiaInput

from energy.clima.lector_pvgis import descargar_clima_pvgis

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

   def ejecutar(self, datos, sizing, *_):

    sf = getattr(datos, "sistema_fv", {}) or {}
    eq = getattr(datos, "equipos", {}) or {}

    # --------------------------------------------------
    # VALIDACIÓN
    # --------------------------------------------------

    if not strings or not getattr(strings, "n_series", None):
        raise ValueError("Strings inválidos para energía")

    # --------------------------------------------------
    # PANEL
    # --------------------------------------------------

    panel = get_panel(eq.get("panel_id"))

    # --------------------------------------------------
    # COORDENADAS (FIX DEFINITIVO)
    # --------------------------------------------------

    lat = getattr(datos, "lat", None)
    lon = getattr(datos, "lon", None)

    if lat is None:
        lat = sf.get("latitud", 14.8)

    if lon is None:
        lon = sf.get("longitud", -86.2)

    # --------------------------------------------------
    # CLIMA
    # --------------------------------------------------

    clima = descargar_clima_pvgis(
        EntradaClimaPVGIS(
            lat=float(lat),
            lon=float(lon),
            startyear=2019,
            endyear=2019
        )
    )

    # --------------------------------------------------
    # INPUT ENERGÍA
    # --------------------------------------------------

    entrada = EnergiaInput(

        # POTENCIA
        pdc_instalada_kw=sizing.pdc_kw,
        pac_nominal_kw=sizing.kw_ac,

        # CLIMA
        clima=clima,
        tilt_deg=sf.get("inclinacion_deg"),

        # CONFIG FV
        paneles_por_string=strings.n_series,
        n_strings_total=strings.n_strings_total,

        # PANEL
        p_panel_w=panel.pmax_w,
        vmp_panel_v=panel.vmp_v,
        voc_panel_v=panel.voc_v,
        imp_panel_a=panel.imp_a,
        isc_panel_a=panel.isc_a,

        coef_potencia=panel.coef_pmax,
        coef_vmp=panel.coef_vmp,
        coef_voc=panel.coef_voc,

        noct_c=getattr(panel, "noct_c", 45.0),

        # PÉRDIDAS
        perdidas_dc_pct=sf.get("perdidas_dc_pct", 0.03),
        perdidas_ac_pct=sf.get("perdidas_ac_pct", 0.02),
        sombras_pct=sf.get("sombras_pct", 0.0),

        # INVERSOR
        eficiencia_inversor=sf.get("eficiencia_inversor", 0.97),
    )

    return ejecutar_motor_energia(entrada)

# ==========================================================
# ADAPTER ENERGÍA (REFORMADO)
# ==========================================================

class EnergiaAdapter:

    def ejecutar(self, datos, sizing, strings):

        sf = getattr(datos, "sistema_fv", {}) or {}
        eq = getattr(datos, "equipos", {}) or {}

        # --------------------------------------------------
        # VALIDACIÓN
        # --------------------------------------------------

        if not strings or not getattr(strings, "n_series", None):
            raise ValueError("Strings inválidos para energía")

        # --------------------------------------------------
        # PANEL (FUENTE REAL)
        # --------------------------------------------------

        panel = get_panel(eq.get("panel_id"))

        # --------------------------------------------------
        # CLIMA 8760
        # --------------------------------------------------

        clima = descargar_clima_pvgis(
            EntradaClimaPVGIS(
                lat=datos.lat,
                lon=datos.lon,
                startyear=2019,
                endyear=2019
            )
        )

        # --------------------------------------------------
        # INPUT ENERGÍA (LIMPIO)
        # --------------------------------------------------

        entrada = EnergiaInput(

            # ---------------- POTENCIA ----------------

            pdc_instalada_kw=sizing.pdc_kw,
            pac_nominal_kw=sizing.kw_ac,

            # ---------------- CLIMA ----------------

            clima=clima,
            tilt_deg=sf.get("inclinacion_deg"),

            # ---------------- CONFIG FV ----------------

            paneles_por_string=strings.n_series,
            n_strings_total=strings.n_strings_total,

            # ---------------- PANEL ----------------

            p_panel_w=panel.pmax_w,
            vmp_panel_v=panel.vmp_v,
            voc_panel_v=panel.voc_v,

            imp_panel_a=panel.imp_a,
            isc_panel_a=panel.isc_a,

            coef_potencia=panel.coef_pmax,
            coef_vmp=panel.coef_vmp,
            coef_voc=panel.coef_voc,

            noct_c=getattr(panel, "noct_c", 45.0),

            # ---------------- PÉRDIDAS ----------------

            perdidas_dc_pct=sf.get("perdidas_dc_pct", 0.03),
            perdidas_ac_pct=sf.get("perdidas_ac_pct", 0.02),
            sombras_pct=sf.get("sombras_pct", 0.0),

            # ---------------- INVERSOR ----------------

            eficiencia_inversor=sf.get("eficiencia_inversor", 0.97),
        )

        return ejecutar_motor_energia(entrada)


# ==========================================================
# ADAPTER NEC
# ==========================================================

class NECAdapter:

    def ejecutar(self, datos, sizing, strings):

        if not isinstance(strings, ResultadoStrings):
            raise ValueError("strings inválido para NEC")

        if not strings.strings:
            raise ValueError("No hay strings")

        sf = getattr(datos, "sistema_fv", {}) or {}

        s0 = strings.strings[0]

        entrada_nec = {

            "electrico": {
                "vac_ll": sf.get("vac", 240),
                "fases": sf.get("fases", 1),
                "fp": sf.get("fp", 1.0),
            },

            "potencia_dc_kw": sizing.pdc_kw,
            "potencia_ac_kw": sizing.kw_ac,

            "vdc_nom": sf.get("vdc_nom", 600),

            "strings": {
                "imp_string_a": s0.imp_string_a,
                "isc_string_a": s0.isc_string_a,
                "strings_por_mppt": 1,
                "n_strings_total": strings.n_strings_total,
            },

            "inversor": {
                "kw_ac": sizing.kw_ac,
                "v_ac_nom_v": sf.get("vac", 240),
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
