from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

# 🔥 SOLO ORQUESTADORES (caja negra)
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.orquestador_electrical import ejecutar_electrical

from core.servicios.sizing import calcular_sizing_unificado


# ==========================================================
# SIZING
# ==========================================================

class SizingAdapter:
    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


# ==========================================================
# PANELES (CAJA NEGRA)
# ==========================================================

class PanelesAdapter:
    def ejecutar(self, datos, sizing):
        """
        core NO arma entradas
        electrical resuelve TODO internamente
        """
        return ejecutar_paneles(
            datos=datos,
            sizing=sizing,
        )


# ==========================================================
# ELECTRICAL (ORQUESTADOR GLOBAL)
# ==========================================================

class ElectricalAdapter:
    def ejecutar(self, *, datos, paneles):
        """
        Adapter que traduce datos → params_conductores
        """

        params = datos.electrical  # ajusta si tu estructura cambia

        return ejecutar_electrical(
            paneles=paneles,
            params_conductores=params,
        )

# ==========================================================
# ENERGÍA (PLACEHOLDER)
# ==========================================================

class EnergiaAdapter:
    def ejecutar(self, datos, sizing, paneles):
        return None


# ==========================================================
# FINANZAS (PLACEHOLDER)
# ==========================================================

class FinanzasAdapter:
    def ejecutar(self, datos, sizing, energia):
        return None


# ==========================================================
# BUILDER
# ==========================================================

def construir_dependencias() -> DependenciasEstudio:

    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=ElectricalAdapter(),  # 🔥 AQUÍ VA TODO ELECTRICAL
        finanzas=FinanzasAdapter(),
    )
