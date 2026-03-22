from __future__ import annotations

"""
DEPENDENCIAS — FV ENGINE (REAL)

Construye el objeto DependenciasEstudio que usa el orquestador
"""

from core.aplicacion.orquestador_estudio import DependenciasEstudio

# ==========================================================
# IMPLEMENTACIONES REALES (AQUÍ VAN TUS CLASES)
# ==========================================================

from core.aplicacion.sizing import SizingAdapter
from core.aplicacion.paneles import PanelesAdapter
from core.aplicacion.nec import NECAdapter
from core.aplicacion.energia import EnergiaAdapter
from core.aplicacion.finanzas import FinanzasAdapter


# ==========================================================
# BUILDER REAL
# ==========================================================

def construir_dependencias() -> DependenciasEstudio:
    """
    Construye TODAS las dependencias del estudio
    """

    return DependenciasEstudio(
        sizing=SizingAdapter(),
        paneles=PanelesAdapter(),
        energia=EnergiaAdapter(),
        nec=NECAdapter(),
        finanzas=FinanzasAdapter(),
    )
