from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

from core.dominio.contrato import StringInfo, ResultadoStrings

from core.servicios.sizing import calcular_sizing_unificado

from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.entrada_panel import EntradaPaneles

from electrical.nec.orquestador_nec import ejecutar_nec

from electrical.catalogos.catalogos import get_panel, get_inversor

from energy.orquestador_energia import ejecutar_motor_energia
from energy.contrato import EnergiaInput

from energy.clima.lector_pvgis import descargar_clima_pvgis, EntradaClimaPVGIS

from core.servicios.finanzas import ejecutar_finanzas


# ==========================================================
# SIZING
# ==========================================================

class SizingAdapter:

    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


# ==========================================================
# PANELES (SOLO STRINGS)
# ==========================================================

class PanelesAdapter:

    def ejecutar(self, datos, sizing, *_):

        eq = getattr(datos, "equipos", {}) or {}
        sf = getattr(datos, "sistema_fv", {}) or {}

        panel = get_panel(eq.get("panel_id"))
        inversor = get_inversor(eq.get("inversor_id"))

        if panel is None:
            raise ValueError("panel_id no definido en equipos")

        if inversor is None:
            raise ValueError("inversor_id no definido en equipos")

        entrada = EntradaPaneles(
            panel=panel,
            inversor=inversor,
            n_paneles_total=sizing.n_paneles,
            n_inversores=sizing.n_inversores,
            t_min_c=sf.get("t_min_c", 10),
            t_oper_c=sf.get("t_oper_c", 45),
            dos_aguas=sf.get("dos_aguas", False),
            objetivo_dc_ac=sf.get("dc_ac_ratio", 1.2),
            pdc_kw_objetivo=None,
        )

        res = ejecutar_paneles(entrada)

        if not res.get("ok", False):
            raise ValueError(f"Error en dominio paneles: {res.get('errores')}")

        strings = []

        for s in res.get("strings", []):
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
# ENERGÍA (8760 REAL)
# ==========================================================

class EnergiaAdapter:

    def ejecutar(self, datos, sizing, strings):

        if not strings or not getattr(strings, "n_series", None):
            raise ValueError("Strings inválidos para energía")

        sf = getattr(datos, "sistema_fv", {}) or {}
        eq = getattr(datos, "equipos", {}) or {}

        panel = get_panel(eq.get("panel_id"))

        if panel is None:
            raise ValueError("panel_id no definido")

        lat = getattr(datos, "lat", None)
        lon = getattr(datos, "lon", None)

        if lat is None:
            lat = sf.get("latitud", 14.8)

        if lon is None:
            lon = sf.get("longitud", -86.2)

        clima = descargar_clima_pvgis(
            EntradaClimaPVGIS(
                lat=float(lat),
                lon=float(lon),
                startyear=2019,
                endyear=2019,
            )
        )

        entrada = EnergiaInput(

            # --------------------------------------------------
            # POTENCIA
            # --------------------------------------------------
            pdc_instalada_kw=sizing.pdc_kw,
            pac_nominal_kw=sizing.kw_ac,

            # --------------------------------------------------
            # 8760
            # --------------------------------------------------
            clima=clima,
            tilt_deg=sf.get("inclinacion_deg") or 10.0,

            # --------------------------------------------------
            # ARREGLO FV
            # --------------------------------------------------
            paneles_por_string=strings.n_series,
            n_strings_total=strings.n_strings_total,

            pmax_stc_w=panel.pmax_w,
            vmp_stc_v=panel.vmp_v,
            voc_stc_v=panel.voc_v,

            coef_pmax_pct_per_c=getattr(panel, "coef_pmax", -0.004),
            coef_vmp_pct_per_c=getattr(panel, "coef_vmp", -0.003),
            coef_voc_pct_per_c=getattr(panel, "coef_voc", -0.002),

            # --------------------------------------------------
            # PÉRDIDAS
            # --------------------------------------------------
            perdidas_dc_pct=sf.get("perdidas_dc_pct", 0.03),
            perdidas_ac_pct=sf.get("perdidas_ac_pct", 0.02),
            sombras_pct=sf.get("sombras_pct", 0.0),

            # --------------------------------------------------
            # INVERSOR
            # --------------------------------------------------
            eficiencia_inversor=sf.get("eficiencia_inversor", 0.97),
        )

        return ejecutar_motor_energia(entrada)


# ==========================================================
# NEC
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
# FINANZAS
# ==========================================================

class FinanzasAdapter:

    def ejecutar(self, datos, sizing, energia):
        return ejecutar_finanzas(datos=datos, sizing=sizing, energia=energia)


# ==========================================================
# FACTORY
# ==========================================================

def construir_dependencias():

    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=NECAdapter(),
        finanzas=FinanzasAdapter(),
    )
