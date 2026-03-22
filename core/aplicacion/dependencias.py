from __future__ import annotations

from core.aplicacion.orquestador_estudio import DependenciasEstudio

# IMPORTS REALES
from electrical.paneles.orquestador_paneles import ejecutar_paneles
from electrical.paneles.entrada_panel import EntradaPaneles
from core.aplicacion.puertos import PuertoNEC
from core.servicios.sizing import calcular_sizing_unificado
from electrical.catalogos import get_panel
from electrical.modelos.inversor import InversorSpec


# ==========================================================
# SIZING
# ==========================================================

class SizingAdapter:
    def ejecutar(self, datos):
        return calcular_sizing_unificado(datos)


# ==========================================================
# PANELES
# ==========================================================

class PanelesAdapter:
    def ejecutar(self, datos, sizing):

        eq = getattr(datos, "equipos", None)
        if not eq:
            raise ValueError("datos.equipos no definido")

        panel_id = eq.get("panel_id")
        panel = get_panel(panel_id)

        if panel is None:
            raise ValueError("Panel no encontrado en catálogo")

        # ✅ INVERSOR REAL
        inversor = sizing.inversor

        if inversor is None:
            raise ValueError("Inversor no definido desde sizing")

        entrada = EntradaPaneles(
            panel=panel,
            inversor=inversor,

            n_paneles_total=sizing.n_paneles,
            n_inversores=sizing.n_inversores,

            t_min_c=10,
            t_oper_c=50,

            objetivo_dc_ac=None,
            pdc_kw_objetivo=sizing.pdc_kw,
        )

        return ejecutar_paneles(entrada)

# ==========================================================
# NEC
# ==========================================================

class NECAdapter:
    def ejecutar(self, datos, sizing, paneles):
        return PuertoNEC().ejecutar(datos, sizing, paneles)


# ==========================================================
# PLACEHOLDERS
# ==========================================================

class EnergiaAdapter:
    def ejecutar(self, datos, sizing, paneles):
        return None


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
        nec=NECAdapter(),
        finanzas=FinanzasAdapter(),
    )
