from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

# ✔ IMPORTS REALES (LOS TUYOS)
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.entrada_panel import EntradaPaneles
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

        entrada = EntradaPaneles(
            datos=datos,
            sizing=sizing
        )

        return ejecutar_paneles(entrada)

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
