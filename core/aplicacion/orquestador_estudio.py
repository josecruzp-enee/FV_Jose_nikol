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

from electrical.paneles.entrada_panel import EntradaPaneles


# ==========================================================
# DEPENDENCIAS
# ==========================================================
@dataclass
class DependenciasEstudio:
    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    electrical: Optional[PuertoNEC] = None
    finanzas: Optional[PuertoFinanzas] = None


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================
def ejecutar_estudio(datos: Any, deps: DependenciasEstudio):

    try:
        sizing = _ejecutar_sizing(datos, deps)

        if not getattr(sizing, "ok", True):
            return ResultadoProyecto(sizing=sizing, strings=None, energia=None, nec=None, financiero=None)

        entrada_paneles = _construir_entrada_paneles(datos, sizing)

        paneles = _ejecutar_paneles(entrada_paneles, deps)

        if not paneles.ok:
            return ResultadoProyecto(sizing=sizing, strings=paneles, energia=None, nec=None, financiero=None)

        energia = _ejecutar_energia(datos, sizing, paneles, deps)

        if not getattr(energia, "ok", True):
            return ResultadoProyecto(sizing=sizing, strings=paneles, energia=energia, nec=None, financiero=None)

        electrico = _ejecutar_electrical(datos, sizing, paneles, deps)

        financiero = _ejecutar_finanzas(datos, sizing, energia, deps)

        return ResultadoProyecto(
            sizing=sizing,
            strings=paneles,
            energia=energia,
            nec=electrico,
            financiero=financiero,
        )

    except Exception:
        import traceback
        print(traceback.format_exc())
        raise


# ==========================================================
# FUNCIONES INTERNAS
# ==========================================================

def _ejecutar_sizing(datos, deps):
    sizing = deps.sizing.ejecutar(datos)

    if sizing is None:
        raise ValueError("Sizing devolvió None")

    return sizing


def _construir_entrada_paneles(datos, sizing):

    from electrical.catalogos.catalogos import get_panel

    equipos = getattr(datos, "equipos", {}) or {}

    panel_id = equipos.get("panel_id")

    if not panel_id:
        raise ValueError("panel_id no definido en datos.equipos")

    panel = get_panel(panel_id)

    if panel is None:
        raise ValueError(f"Panel no encontrado en catálogo: {panel_id}")

    inversor = sizing.inversor

    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        n_inversores=sizing.n_inversores,
        n_paneles_total=sizing.n_paneles,
    )


def _ejecutar_paneles(entrada_paneles, deps):

    resultado = deps.paneles.ejecutar(entrada_paneles)

    if resultado is None:
        raise ValueError("Paneles devolvió None")

    return resultado


def _ejecutar_energia(datos, sizing, paneles, deps):

    energia = deps.energia.ejecutar(datos, sizing, paneles)

    if energia is None:
        raise ValueError("Energía devolvió None")

    return energia


def _ejecutar_electrical(datos, sizing, paneles, deps):

    if not deps.electrical:
        print("⚠ No hay módulo electrical")
        return None

    print("🔥 LLAMANDO ELECTRICAL")

    resultado = deps.electrical.ejecutar(
        datos=datos,
        paneles=paneles,
        sizing=sizing,
    )

    print("⚡ RESULTADO ELECTRICAL:", resultado)

    return resultado
def _ejecutar_finanzas(datos, sizing, energia, deps):

    if not deps.finanzas:
        return None

    return deps.finanzas.ejecutar(datos, sizing, energia)
