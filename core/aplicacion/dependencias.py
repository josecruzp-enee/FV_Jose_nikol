from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.dominio.contrato import ResultadoProyecto

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
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
from electrical.catalogos.catalogos import get_inversor as obtener_inversor

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
    nec: Optional[PuertoNEC] = None
    finanzas: Optional[PuertoFinanzas] = None


# ==========================================================
# ADAPTERS
# ==========================================================

class SizingAdapter:
    def ejecutar(self, datos):
        resultado = calcular_sizing_unificado(datos)

        if resultado is None:
            raise ValueError("Sizing devolvió None desde servicio")

        return resultado


class PanelesAdapter:
    def ejecutar(self, datos, sizing):

        if sizing is None:
            raise ValueError("Sizing es None en PanelesAdapter")

        if not hasattr(datos, "equipos") or not isinstance(datos.equipos, dict):
            raise ValueError("datos.equipos no definido o inválido")

        panel_id = datos.equipos.get("panel_id")
        inversor_id = datos.equipos.get("inversor_id")

        if not panel_id:
            raise ValueError("panel_id no definido")

        if not inversor_id:
            raise ValueError("inversor_id no definido")

        panel = obtener_panel(panel_id)
        inversor = obtener_inversor(inversor_id)

        if panel is None:
            raise ValueError(f"Panel no encontrado: {panel_id}")

        if inversor is None:
            raise ValueError(f"Inversor no encontrado: {inversor_id}")

        entrada = EntradaPaneles(
            panel=panel,
            inversor=inversor,
            n_paneles_total=getattr(sizing, "n_paneles", None),
            n_inversores=getattr(sizing, "n_inversores", None),
            t_min_c=-10.0,
            t_oper_c=45.0,
        )

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

        from energy.orquestador_energia import ejecutar_motor_energia

        # ==================================================
        # VALIDACIÓN PANEL
        # ==================================================
        if paneles is None or not getattr(paneles, "ok", False):
            raise ValueError("Paneles inválido para energía")

        # ==================================================
        # VALIDACIÓN KW_AC (CRÍTICO)
        # ==================================================
        kw_ac = getattr(sizing, "kw_ac", None)

        if not kw_ac or kw_ac <= 0:
            raise ValueError("kw_ac inválido para energía")

        # ==================================================
        # VALIDACIÓN LAT/LON
        # ==================================================
        lat = getattr(datos, "lat", None)
        lon = getattr(datos, "lon", None)

        if lat is None or lon is None:
            raise ValueError("Faltan lat/lon para cálculo de energía")

        # ==================================================
        # CLIMA
        # ==================================================
        clima = descargar_clima_pvgis(
            EntradaClimaPVGIS(
                lat=lat,
                lon=lon,
            )
        )

        if clima is None:
            raise ValueError("Clima no disponible")

        # ==================================================
        # INPUT ENERGÍA
        # ==================================================
        entrada = EnergiaInput(
            paneles=paneles,
            pac_nominal_kw=kw_ac,
            clima=clima,

            tilt_deg=15,
            azimut_deg=180,

            perdidas_dc_pct=0.05,
            sombras_pct=0.02,
            eficiencia_inversor=0.98,
            perdidas_ac_pct=0.02,
        )

        print("DEBUG ENERGIA INPUT:", entrada)

        resultado = ejecutar_motor_energia(entrada)

        print("DEBUG ENERGIA OUTPUT:", resultado)

        if resultado is None:
            raise ValueError("Energía devolvió None")

        if not resultado.ok:
            raise ValueError(f"Energía inválida: {resultado.errores}")

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
        nec=ElectricalAdapter(),
        finanzas=FinanzasAdapter(),
    )


# ==========================================================
# ORQUESTADOR (ORDEN CORRECTO)
# ==========================================================

def ejecutar_estudio(
    datos: Any,
    deps: DependenciasEstudio,
):

    print("\n==============================")
    print("FV ENGINE — INICIO ESTUDIO")
    print("==============================")

    try:

        # ------------------------------------------------------
        # 1. SIZING
        # ------------------------------------------------------
        print("\n[1] EJECUTANDO SIZING")

        sizing = deps.sizing.ejecutar(datos)

        if sizing is None:
            raise ValueError("Sizing devolvió None")

        if getattr(sizing, "ok", True) is False:
            return ResultadoProyecto(
                sizing=sizing,
                strings=None,
                energia=None,
                nec=None,
                financiero=None,
            )

        # ------------------------------------------------------
        # 2. PANEL / STRINGS
        # ------------------------------------------------------
        print("\n[2] EJECUTANDO PANEL / STRINGS")

        resultado_paneles = deps.paneles.ejecutar(datos, sizing)

        if resultado_paneles is None:
            raise ValueError("Paneles devolvió None")

        if not resultado_paneles.ok:
            return ResultadoProyecto(
                sizing=sizing,
                strings=resultado_paneles,
                energia=None,
                nec=None,
                financiero=None,
            )

        # ------------------------------------------------------
        # 3. ENERGÍA (🔥 PRIMERO)
        # ------------------------------------------------------
        print("\n[3] EJECUTANDO ENERGIA")

        energia = deps.energia.ejecutar(
            datos,
            sizing,
            resultado_paneles,
        )

        if energia is None:
            raise ValueError("Energía devolvió None")

        if getattr(energia, "ok", True) is False:
            return ResultadoProyecto(
                sizing=sizing,
                strings=resultado_paneles,
                energia=energia,
                nec=None,
                financiero=None,
            )

        # ------------------------------------------------------
        # 4. ELECTRICAL / NEC
        # ------------------------------------------------------
        print("\n[4] CALCULOS ELECTRICOS")

        resultado_electrico = None

        if deps.nec:
            resultado_electrico = deps.nec.ejecutar(
                datos=datos,
                paneles=resultado_paneles,
            )

            if resultado_electrico is None:
                raise ValueError("Electrical devolvió None")

        # ------------------------------------------------------
        # 5. FINANZAS
        # ------------------------------------------------------
        print("\n[5] EJECUTANDO FINANZAS")

        financiero = None

        if deps.finanzas:
            financiero = deps.finanzas.ejecutar(
                datos,
                sizing,
                energia,
            )

        # ------------------------------------------------------
        # VALIDACIÓN FINAL
        # ------------------------------------------------------
        if energia is None:
            raise ValueError("ENERGÍA NO GENERADA")

        # ------------------------------------------------------
        # RESULTADO FINAL
        # ------------------------------------------------------
        resultado = ResultadoProyecto(
            sizing=sizing,
            strings=resultado_paneles,
            energia=energia,
            nec=resultado_electrico,
            financiero=financiero,
        )

        print("\n==============================")
        print("FV ENGINE — FIN ESTUDIO")
        print("==============================")

        return resultado

    except Exception:

        import traceback

        print("\n🔥 ERROR REAL EN ORQUESTADOR 🔥")
        print(traceback.format_exc())

        raise
