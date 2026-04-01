from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ==========================================================
# PUERTOS
# ==========================================================

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoElectrical,
    PuertoFinanzas,
)

# ==========================================================
# SERVICIOS / ORQUESTADORES
# ==========================================================

from core.servicios.sizing import calcular_sizing_unificado
from core.aplicacion.multizona import ejecutar_multizona  # ✅ CORRECTO
from electrical.orquestador_electrical import ejecutar_electrical
from energy.orquestador_energia import ejecutar_energia
from core.servicios.finanzas import ejecutar_finanzas

# ==========================================================
# INPUTS / CONTRATOS
# ==========================================================

from electrical.paneles.entrada_panel import EntradaPaneles


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
# ADAPTER: PANELES (MULTIZONA)
# ==========================================================

from electrical.paneles.orquestador_paneles import ejecutar_paneles
from core.aplicacion.multizona import ejecutar_multizona


class PanelesAdapter:

    def ejecutar(self, entrada: EntradaPaneles):

        if entrada is None:
            raise ValueError("EntradaPaneles es None")

        modo = getattr(entrada, "modo", None)

        if not modo:
            raise ValueError("EntradaPaneles sin modo")

        # ==================================================
        # ROUTING CORRECTO
        # ==================================================
        if modo == "multizona":
            resultado = ejecutar_multizona(entrada)
        else:
            resultado = ejecutar_paneles(entrada)

        # ==================================================
        # VALIDACIÓN
        # ==================================================
        if resultado is None:
            raise ValueError("Paneles devolvió None")

        if not getattr(resultado, "ok", True):
            raise ValueError(f"Error en paneles: {resultado.errores}")

        return resultado


# ==========================================================
# ADAPTER: ELECTRICAL
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
# ADAPTER: ENERGÍA
# ==========================================================

class EnergiaAdapter:

    def ejecutar(self, datos, sizing, paneles):

        if datos is None:
            raise ValueError("datos es None en energía")

        if sizing is None:
            raise ValueError("sizing es None en energía")

        if paneles is None:
            raise ValueError("paneles es None en energía")

        resultado = ejecutar_energia(datos, sizing, paneles)

        if resultado is None:
            raise ValueError("Energía devolvió None")

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
