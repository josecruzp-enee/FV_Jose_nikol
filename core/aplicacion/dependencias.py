from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.dominio.contrato import ResultadoProyecto

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoElectrical,
    PuertoFinanzas,
)

# ==========================================================
# IMPORTS
# ==========================================================

from core.servicios.sizing import calcular_sizing_unificado
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.orquestador_electrical import ejecutar_electrical
from energy.orquestador_energia import ejecutar_motor_energia as ejecutar_energia
from core.servicios.finanzas import ejecutar_finanzas

from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos.catalogos import get_panel as obtener_panel

from energy.contrato import EnergiaInput

from energy.clima.lector_pvgis import (
    descargar_clima_pvgis,
    EntradaClimaPVGIS,
)

# ==========================================================
# DEPENDENCIAS
# ==========================================================

@dataclass
class DependenciasEstudio:
    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    electrical: Optional[PuertoElectrical]
    finanzas: Optional[PuertoFinanzas]


# ==========================================================
# ADAPTERS
# ==========================================================

class SizingAdapter:
    def ejecutar(self, datos):
        resultado = calcular_sizing_unificado(datos)
        if resultado is None:
            raise ValueError("Sizing devolvió None")
        return resultado


class PanelesAdapter:

    def ejecutar(self, entrada: EntradaPaneles):

        if entrada is None:
            raise ValueError("EntradaPaneles es None")

        resultado = ejecutar_paneles(entrada)

        if resultado is None:
            raise ValueError("Paneles devolvió None")

        return resultado


class ElectricalAdapter:
    def ejecutar(self, datos, paneles, sizing):

        resultado = ejecutar_electrical(
            datos=datos,
            paneles=paneles,
            sizing=sizing,
        )

        if resultado is None:
            raise ValueError("Electrical devolvió None")

        return resultado


class EnergiaAdapter:

    def ejecutar(self, datos, sizing, paneles):

        lat = datos.lat
        lon = datos.lon

        clima = descargar_clima_pvgis(
            EntradaClimaPVGIS(lat=lat, lon=lon)
        )

        n_series = paneles.recomendacion.n_series
        n_strings = paneles.array.n_strings_total
        pdc_kw = paneles.array.potencia_dc_w / 1000

        panel_spec = obtener_panel(datos.equipos.get("panel_id"))

        # =========================
        # FIX: INPUT COMPLETO
        # =========================
        entrada = EnergiaInput(
            n_series=n_series,
            n_strings=n_strings,
            pdc_kw=pdc_kw,
            panel=panel_spec,
            pac_nominal_kw=sizing.kw_ac,
            clima=clima,

            # 🔥 CAMPOS FALTANTES
            tilt_deg=getattr(datos, "tilt_deg", 15),
            azimut_deg=getattr(datos, "azimut_deg", 180),
            perdidas_dc_frac=getattr(datos, "perdidas_dc_frac", 0.14),
            sombras_frac=getattr(datos, "sombras_frac", 0.0),
            eficiencia_inversor=getattr(datos, "eficiencia_inversor", 0.97),
            perdidas_ac_frac=getattr(datos, "perdidas_ac_frac", 0.02),
        )

        resultado = ejecutar_energia(entrada)

        if not resultado.ok:
            raise ValueError("Energía inválida")

        return resultado


class FinanzasAdapter:
    def ejecutar(self, datos, sizing, energia):

        resultado = ejecutar_finanzas(
            datos=datos,
            sizing=sizing,
            energia=energia,
        )

        if resultado is None:
            raise ValueError("Finanzas devolvió None")

        return resultado


# ==========================================================
# FACTORY
# ==========================================================

def construir_dependencias() -> DependenciasEstudio:
    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        electrical=ElectricalAdapter(),
        finanzas=FinanzasAdapter(),
    )


# ==========================================================
# ORQUESTADOR
# ==========================================================

def ejecutar_estudio(
    datos: Any,
    deps: DependenciasEstudio,
):

    try:

        # ==================================================
        # 1. SIZING
        # ==================================================
        sizing = deps.sizing.ejecutar(datos)

        # ==================================================
        # 2. PANELES (FIX: entrada definida)
        # ==================================================
        entrada_paneles = EntradaPaneles(
            datos=datos,
            sizing=sizing,
        )

        resultado_paneles = deps.paneles.ejecutar(entrada_paneles)

        # ==================================================
        # 3. ENERGÍA
        # ==================================================
        energia = deps.energia.ejecutar(
            datos,
            sizing,
            resultado_paneles,
        )

        # ==================================================
        # 4. ELECTRICAL
        # ==================================================
        resultado_electrico = None

        if deps.electrical:
            resultado_electrico = deps.electrical.ejecutar(
                datos=datos,
                paneles=resultado_paneles,
                sizing=sizing,
            )

        # ==================================================
        # 5. FINANZAS
        # ==================================================
        financiero = None

        if deps.finanzas:
            financiero = deps.finanzas.ejecutar(
                datos,
                sizing,
                energia,
            )

        # ==================================================
        # RESULTADO FINAL
        # ==================================================
        return ResultadoProyecto(
            sizing=sizing,
            strings=resultado_paneles,
            energia=energia,
            electrical=resultado_electrico,
            financiero=financiero,
        )

    except Exception:
        import traceback
        print(traceback.format_exc())
        raise
