from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, List

from core.dominio.contrato import ResultadoProyecto

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoElectrical,
    PuertoFinanzas,
)

# ==========================================================
# IMPORTS SERVICIOS
# ==========================================================

from core.servicios.sizing import calcular_sizing_unificado
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.orquestador_electrical import ejecutar_electrical
from energy.orquestador_energia import ejecutar_motor_energia as ejecutar_energia
from core.servicios.finanzas import ejecutar_finanzas

# ==========================================================
# IMPORTS DOMINIO
# ==========================================================

from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos.catalogos import get_panel
from energy.contrato import EnergiaInput

from energy.clima.lector_pvgis import (
    descargar_clima_pvgis,
    EntradaClimaPVGIS,
)

# 🔥 NUEVOS
from core.aplicacion.helpers_zonas import extraer_zonas
from core.aplicacion.builder_paneles import construir_entrada_paneles

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


# ==========================================================
# 🔥 ENERGÍA (CORREGIDO MULTIZONA)
# ==========================================================

class EnergiaAdapter:

    def ejecutar(self, datos, sizing, paneles):

        lat = datos.lat
        lon = datos.lon

        clima = descargar_clima_pvgis(
            EntradaClimaPVGIS(lat=lat, lon=lon)
        )

        # =========================
        # 🔥 SOPORTE MULTIZONA
        # =========================
        if isinstance(paneles, list):
            panel_ref = paneles[0]   # usamos referencia base
        else:
            panel_ref = paneles

        n_series = panel_ref.recomendacion.n_series
        n_strings = panel_ref.array.n_strings_total
        pdc_kw = panel_ref.array.potencia_dc_w / 1000

        panel_spec = get_panel(datos.equipos.get("panel_id"))

        entrada = EnergiaInput(
            n_series=n_series,
            n_strings=n_strings,
            pdc_kw=pdc_kw,
            panel=panel_spec,
            pac_nominal_kw=sizing.kw_ac,
            clima=clima,

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
