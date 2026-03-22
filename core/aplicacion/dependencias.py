from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

from core.dominio.contrato import StringInfo, ResultadoStrings

from core.servicios.sizing import calcular_sizing_unificado

from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.entrada_panel import EntradaPaneles

from electrical.nec.orquestador_nec import ejecutar_nec

from electrical.catalogos.catalogos import get_panel, get_inversor

from energy.clima.lector_pvgis import descargar_clima_pvgis, EntradaClimaPVGIS

from core.servicios.finanzas import ejecutar_finanzas


# ==========================================================
# SIZING
# ==========================================================

class SizingAdapter:

    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


# ==========================================================
# PANELES (DOMINIO REAL)
# ==========================================================

class PanelesAdapter:

    def ejecutar(self, datos, sizing, *_):

        eq = getattr(datos, "equipos", {}) or {}
        sf = getattr(datos, "sistema_fv", {}) or {}

        panel = get_panel(eq.get("panel_id"))
        inversor = get_inversor(eq.get("inversor_id"))

        if panel is None:
            raise ValueError("panel_id no definido")

        if inversor is None:
            raise ValueError("inversor_id no definido")

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

        resultado_paneles = ejecutar_paneles(entrada)

        if not resultado_paneles.ok:
            raise ValueError("Error en paneles")

        return resultado_paneles


# ==========================================================
# ENERGÍA (SIN CICLOS)
# ==========================================================

class EnergiaAdapter:

    def ejecutar(self, datos, sizing, paneles):

        # 🔥 IMPORTS LOCALES → evita ciclos
        from energy.orquestador_energia import ejecutar_motor_energia
        from energy.contrato import EnergiaInput

        sf = getattr(datos, "sistema_fv", {}) or {}

        # --------------------------------------------------
        # UBICACIÓN
        # --------------------------------------------------
        lat = getattr(datos, "lat", None) or sf.get("latitud", 14.8)
        lon = getattr(datos, "lon", None) or sf.get("longitud", -86.2)

        # --------------------------------------------------
        # CLIMA 8760
        # --------------------------------------------------
        clima = descargar_clima_pvgis(
            EntradaClimaPVGIS(
                lat=float(lat),
                lon=float(lon),
                startyear=2019,
                endyear=2019,
            )
        )

        # --------------------------------------------------
        # ENTRADA ENERGÍA
        # --------------------------------------------------
        entrada = EnergiaInput(
            paneles=paneles,
            pac_nominal_kw=sizing.kw_ac,
            tilt_deg=sf.get("inclinacion_deg", 10.0),
            azimut_deg=sf.get("azimut_deg", 180.0),
            clima=clima,
            perdidas_dc_pct=sf.get("perdidas_dc_pct", 0.03),
            perdidas_ac_pct=sf.get("perdidas_ac_pct", 0.02),
            sombras_pct=sf.get("sombras_pct", 0.0),
            eficiencia_inversor=sf.get("eficiencia_inversor", 0.97),
        )

        return ejecutar_motor_energia(entrada)


# ==========================================================
# NEC
# ==========================================================
class NECAdapter:

    def ejecutar(self, datos, sizing, paneles):

        sf = getattr(datos, "sistema_fv", {}) or {}

        if not paneles.strings:
            raise ValueError("No hay strings")

        # --------------------------------------------------
        # INVERSOR TIPADO
        # --------------------------------------------------

        class InversorInput:
            def __init__(self, kw_ac, vac, fases, fp):
                self.kw_ac = kw_ac
                self.v_ac_nom_v = vac
                self.fases = fases
                self.fp = fp

        inversor = InversorInput(
            kw_ac=sizing.kw_ac,
            vac=sf.get("vac", 240),
            fases=sf.get("fases", 1),
            fp=sf.get("fp", 1.0),
        )

        # --------------------------------------------------
        # PARÁMETROS CONDUCTORES
        # --------------------------------------------------

        class ParamsConductores:
            def __init__(self, vdc, vac, l_dc, l_ac, vd_dc, vd_ac):
                self.vdc = vdc
                self.vac = vac
                self.l_dc = l_dc
                self.l_ac = l_ac
                self.vd_dc = vd_dc
                self.vd_ac = vd_ac

        params = ParamsConductores(
            vdc=paneles.vmp_string_v,
            vac=sf.get("vac", 240),
            l_dc=sf.get("dist_dc_m", 10),
            l_ac=sf.get("dist_ac_m", 10),
            vd_dc=sf.get("vd_dc_pct", 2.0),
            vd_ac=sf.get("vd_ac_pct", 2.0),
        )

        # --------------------------------------------------
        # EJECUTAR INGENIERÍA ELÉCTRICA
        # --------------------------------------------------

        return ejecutar_ingenieria_electrica(
            datos_strings=paneles,                 # ResultadoPaneles
            datos_inversor=inversor,
            n_strings=paneles.array.n_strings_total,
            params_conductores=params,
        )
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
