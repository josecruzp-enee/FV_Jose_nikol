from __future__ import annotations

"""
DEPENDENCIAS — FV ENGINE (REAL, SIN INVENTOS)
"""

from core.aplicacion.orquestador_estudio import DependenciasEstudio

# ==========================================================
# IMPORTS REALES (AJUSTA SOLO SI CAMBIAN NOMBRES)
# ==========================================================

from electrical.paneles.orquestador import ejecutar_paneles
from core.aplicacion.puerto_nec import PuertoNEC

# ⚠️ IMPORTANTE:
# si tienes funciones reales de energía / finanzas, cámbialas aquí
# si no, se dejan como passthrough


# ==========================================================
# ADAPTERS REALES
# ==========================================================

class SizingAdapter:
    def ejecutar(self, datos):
        # 🔴 CLAVE:
        # Tú ya traes el sizing desde antes (UI / estado)
        # NO lo vuelvas a calcular aquí
        return datos.sizing


class PanelesAdapter:
    def ejecutar(self, datos, sizing):
        return ejecutar_paneles(datos, sizing)


class NECAdapter:
    def ejecutar(self, datos, sizing, paneles):
        return PuertoNEC().ejecutar(datos, sizing, paneles)


class EnergiaAdapter:
    def ejecutar(self, datos, sizing, paneles):
        # 🔴 TEMPORAL — no romper flujo
        return None


class FinanzasAdapter:
    def ejecutar(self, datos, sizing, energia):
        # 🔴 TEMPORAL
        return None


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
