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

# 🔥 IMPORTS REALES
from core.servicios.sizing import calcular_sizing_unificado
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.orquestador_electrical import ejecutar_electrical
from energy.orquestador_energia import ejecutar_motor_energia as ejecutar_energia
from core.servicios.finanzas import ejecutar_finanzas

# 🔥 PANEL DTO + CATÁLOGOS
from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos.catalogos import get_panel as obtener_panel
from electrical.catalogos.catalogos import get_inversor as obtener_inversor

# 🔥 ENERGÍA DTO
from energy.contrato import EnergiaInput


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
            n_inversores=1,
            t_min_c=-10.0,
            t_oper_c=45.0,
        )

        resultado = ejecutar_paneles(entrada)

        if resultado is None:
            raise ValueError("Paneles devolvió None")

        return resultado


class ElectricalAdapter:
    def ejecutar(self, datos, paneles):
        resultado = ejecutar_electrical(datos=datos, paneles=paneles)

        if resultado is None:
            raise ValueError("Electrical devolvió None")

        return resultado


class EnergiaAdapter:
    def ejecutar(self, datos, sizing, paneles):

        if paneles is None or not getattr(paneles, "ok", False):
            raise ValueError("Paneles inválido para energía")

        entrada = EnergiaInput(
            paneles=paneles,
            pac_nominal_kw=getattr(sizing, "kw_ac", 0),

            # 🔥 puedes mejorar luego con clima real
            clima=datos,

            tilt_deg=15,
            azimut_deg=180,

            perdidas_dc_pct=0.05,
            sombras_pct=0.02,
            eficiencia_inversor=0.98,
            perdidas_ac_pct=0.02,
        )

        resultado = ejecutar_energia(entrada)

        if resultado is None:
            raise ValueError("Energía devolvió None")

        return resultado


class FinanzasAdapter:
    def ejecutar(self, datos, sizing, energia):
        resultado = ejecutar_finanzas(datos, sizing, energia)

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
# ORQUESTADOR
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
        # 2. PANELES
        # ------------------------------------------------------
        print("\n[2] EJECUTANDO PANEL / STRINGS")

        resultado_paneles = deps.paneles.ejecutar(datos, sizing)

        if not resultado_paneles.ok:
            return ResultadoProyecto(
                sizing=sizing,
                strings=resultado_paneles,
                energia=None,
                nec=None,
                financiero=None,
            )

        # ------------------------------------------------------
        # 3. ELECTRICAL
        # ------------------------------------------------------
        print("\n[3] CALCULOS ELECTRICOS")

        resultado_electrico = None

        if deps.nec:
            resultado_electrico = deps.nec.ejecutar(
                datos=datos,
                paneles=resultado_paneles,
            )

            if not resultado_electrico.ok:
                return ResultadoProyecto(
                    sizing=sizing,
                    strings=resultado_paneles,
                    energia=None,
                    nec=resultado_electrico,
                    financiero=None,
                )

        # ------------------------------------------------------
        # 4. ENERGÍA
        # ------------------------------------------------------
        print("\n[4] EJECUTANDO ENERGIA")

        energia = deps.energia.ejecutar(
            datos,
            sizing,
            resultado_paneles,
        )

        if getattr(energia, "ok", True) is False:
            return ResultadoProyecto(
                sizing=sizing,
                strings=resultado_paneles,
                energia=energia,
                nec=resultado_electrico,
                financiero=None,
            )

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
