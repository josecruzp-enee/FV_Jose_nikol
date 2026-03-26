from __future__ import annotations

"""
BUILDER DE ENTRADA — PANELES (MULTIZONA READY)

✔ Sin dependencia de catalogos externos
✔ Usa catálogo interno
✔ Compatible con tu arquitectura actual
✔ No calcula nada
"""

from typing import Any

from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec

# 🔥 NUEVO
from electrical.catalogos.catalogos import get_panel, get_inversor


# ==========================================================
# BUILDER LEGACY
# ==========================================================
def construir_entrada_paneles(datos: Any, sizing, catalogos=None) -> EntradaPaneles:
    """
    Construcción clásica (una sola zona).
    """

    # 🔥 datos es objeto
    equipos = getattr(datos, "equipos", {}) or {}

    panel_id = equipos.get("panel_id")
    inversor_id = getattr(sizing, "inversor_id", None)

    panel: PanelSpec = get_panel(panel_id)
    inversor: InversorSpec = get_inversor(inversor_id)

    if panel is None:
        raise ValueError(f"Panel no encontrado: {panel_id}")

    if inversor is None:
        raise ValueError(f"Inversor no encontrado: {inversor_id}")

    modo = getattr(datos, "modo_dimensionado", "consumo")

    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo=str(modo).strip().lower(),
        n_paneles_total=getattr(datos, "n_paneles", None),
        t_min_c=getattr(sizing, "t_min_c", 25.0),
        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
        dos_aguas=getattr(sizing, "dos_aguas", False),
        objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
        pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
        n_inversores=getattr(sizing, "n_inversores", 1),
    )


# ==========================================================
# BUILDER MULTIZONA
# ==========================================================
def construir_entrada_panel_desde_zona(z, sizing, catalogos=None) -> EntradaPaneles:
    """
    Construye EntradaPaneles para una zona individual.
    """

    panel_id = getattr(z, "panel_id", None)
    inversor_id = getattr(sizing, "inversor_id", None)

    panel: PanelSpec = get_panel(panel_id)
    inversor: InversorSpec = get_inversor(inversor_id)

    if panel is None:
        raise ValueError(f"Panel no encontrado: {panel_id}")

    if inversor is None:
        raise ValueError("Inversor no definido en sizing")

    base_kwargs = dict(
        panel=panel,
        inversor=inversor,
        t_min_c=getattr(sizing, "t_min_c", 25.0),
        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
        dos_aguas=getattr(sizing, "dos_aguas", False),
        objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
        pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
        n_inversores=getattr(sizing, "n_inversores", 1),
    )

    # -------------------------
    # MODO AREA
    # -------------------------
    if z.modo == "area":

        return EntradaPaneles(
            modo="area",
            n_paneles_total=None,
            **base_kwargs,
        )

    # -------------------------
    # MODO MANUAL
    # -------------------------
    elif z.modo == "manual":

        if z.paneles_manual is None:
            raise ValueError(f"Zona {z.nombre} sin paneles")

        return EntradaPaneles(
            modo="manual",
            n_paneles_total=z.paneles_manual,
            **base_kwargs,
        )

    # -------------------------
    # MODO CONSUMO
    # -------------------------
    elif z.modo == "consumo":

        return EntradaPaneles(
            modo="consumo",
            n_paneles_total=None,
            **base_kwargs,
        )

    else:
        raise ValueError(f"Modo inválido en zona {z.nombre}: {z.modo}")
