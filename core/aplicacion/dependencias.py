from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

# ✔ IMPORTS REALES (LOS TUYOS)
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from core.aplicacion.puertos import PuertoNEC
from core.servicios.sizing import calcular_sizing_unificado


# ==========================================================
# ADAPTERS
# ==========================================================

class SizingAdapter:
    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)

class PanelesAdapter:
    def ejecutar(self, datos, sizing):
        return ejecutar_paneles(datos, sizing)


class NECAdapter:
    def ejecutar(self, datos, sizing, paneles):
        return PuertoNEC().ejecutar(datos, sizing, paneles)


class EnergiaAdapter:
    def ejecutar(self, datos, sizing, paneles):
        return None  # temporal


class FinanzasAdapter:
    def ejecutar(self, datos, sizing, energia):
        return None  # temporal


# ==========================================================
# BUILDER
# ==========================================================

def construir_dependencias() -> DependenciasEstudio:

    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=NECAdapter(),
        finanzas=FinanzasAdapter(),
    )
