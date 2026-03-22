from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

# ✔ IMPORTS REALES
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.entrada_panel import EntradaPaneles
from core.aplicacion.puertos import PuertoNEC
from core.servicios.sizing import calcular_sizing_unificado
from electrical.catalogos import get_panel


# ==========================================================
# ADAPTERS
# ==========================================================

class SizingAdapter:
    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


class PanelesAdapter:
    def ejecutar(self, datos, sizing):

        # --------------------------------------------------
        # PANEL
        # --------------------------------------------------

        eq = getattr(datos, "equipos", {}) or {}
        panel_id = eq.get("panel_id")

        panel = get_panel(panel_id)

        if panel is None:
            raise ValueError("Panel no encontrado")

        # --------------------------------------------------
        # ENTRADA PANELES
        # --------------------------------------------------

        entrada = EntradaPaneles(
            panel=panel,
            inversor=None,  # 🔥 FIX DEFINITIVO

            n_paneles_total=sizing.n_paneles,
            n_inversores=sizing.n_inversores,

            t_min_c=10,
            t_oper_c=50,

            objetivo_dc_ac=None,
            pdc_kw_objetivo=sizing.pdc_kw,
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
