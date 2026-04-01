from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoElectrical,
    PuertoFinanzas,
)

# ==========================================================
# SERVICIOS
# ==========================================================

from core.servicios.sizing import calcular_sizing_unificado
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.orquestador_electrical import ejecutar_electrical
from energy.orquestador_energia import ejecutar_motor_energia as ejecutar_energia
from core.servicios.finanzas import ejecutar_finanzas

# ==========================================================
# DOMINIO / INPUTS
# ==========================================================

from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos.catalogos import get_panel
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
# ADAPTER: SIZING
# ==========================================================

class SizingAdapter:
    def ejecutar(self, datos):

        if datos is None:
            raise ValueError("Datosproyecto es None")

        resultado = calcular_sizing_unificado(datos)

        if resultado is None:
            raise ValueError("Sizing devolvió None")

        return resultado


# ==========================================================
# ADAPTER: PANELES
# ==========================================================

class PanelesAdapter:
    def ejecutar(self, entrada: EntradaPaneles):

        if entrada is None:
            raise ValueError("EntradaPaneles es None")

        resultado = ejecutar_paneles(entrada)

        if resultado is None:
            raise ValueError("Paneles devolvió None")

        return resultado


# ==========================================================
# ADAPTER: ELECTRICAL (RÍGIDO)
# ==========================================================

class ElectricalAdapter:

    def ejecutar(
        self,
        *,
        datos,
        paneles,
        sizing,
    ):

        if datos is None:
            raise ValueError("datos es None en electrical")

        if paneles is None:
            raise ValueError("paneles es None en electrical")

        if sizing is None:
            raise ValueError("sizing es None en electrical")

        resultado = ejecutar_electrical(
            datos=datos,
            paneles=paneles,
            sizing=sizing,
        )

        if resultado is None:
            raise ValueError("Electrical devolvió None")

        return resultado


# ==========================================================
# ADAPTER: ENERGÍA (RÍGIDO Y CONSISTENTE)
# ==========================================================

class EnergiaAdapter:

    def ejecutar(self, datos, sizing, paneles):

        if datos is None:
            raise ValueError("datos es None en energía")

        if sizing is None:
            raise ValueError("sizing es None en energía")

        if paneles is None:
            raise ValueError("paneles es None en energía")

        # -----------------------------
        # VALIDACIÓN UBICACIÓN
        # -----------------------------
        lat = datos.lat
        lon = datos.lon

        if lat == 0 and lon == 0:
            raise ValueError("Lat/Lon inválidos (0,0) → PVGIS fallará")

        # -----------------------------
        # CLIMA
        # -----------------------------
        clima = descargar_clima_pvgis(
            EntradaClimaPVGIS(lat=lat, lon=lon)
        )

        if clima is None:
            raise ValueError("Clima PVGIS devolvió None")

        # -----------------------------
        # PANEL (🔥 FIX DICT)
        # -----------------------------
        if not datos.equipos:
            raise ValueError("datos.equipos no definido")

        panel_id = datos.equipos.get("panel_id")

        if not panel_id:
            raise ValueError("panel_id no definido en equipos")

        panel_spec = get_panel(panel_id)

        if panel_spec is None:
            raise ValueError(f"Panel no encontrado: {panel_id}")

        # -----------------------------
        # DATOS ARRAY
        # -----------------------------
        n_series = paneles.recomendacion.n_series
        n_strings = paneles.array.n_strings_total
        pdc_kw = paneles.array.potencia_dc_w / 1000

        # -----------------------------
        # INPUT ENERGÍA
        # -----------------------------
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

        if resultado is None:
            raise ValueError("Energía devolvió None")

        if not resultado.ok:
            raise ValueError("Resultado energía inválido")

        return resultado


# ==========================================================
# ADAPTER: FINANZAS
# ==========================================================

class FinanzasAdapter:
    def ejecutar(self, datos, sizing, energia):

        if datos is None:
            raise ValueError("datos es None en finanzas")

        if sizing is None:
            raise ValueError("sizing es None en finanzas")

        if energia is None:
            raise ValueError("energia es None en finanzas")

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
