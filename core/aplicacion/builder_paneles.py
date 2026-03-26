from __future__ import annotations

"""
BUILDER DE ENTRADA — PANELES (MULTIZONA READY)

✔ Compatible con EntradaPaneles actual
✔ No rompe modo legacy
✔ No calcula nada (solo construye contrato)
✔ Usa objetos reales PanelSpec / InversorSpec
"""

from typing import Any

from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


# ==========================================================
# BUILDER LEGACY (YA EXISTENTE)
# ==========================================================
def construir_entrada_paneles(datos: Any, sizing, catalogos) -> EntradaPaneles:
    """
    Construcción clásica (una sola zona).
    """

    panel: PanelSpec = catalogos.obtener_panel(datos.get("panel_id"))
    inversor: InversorSpec = catalogos.obtener_inversor(sizing.inversor_id)

    if panel is None:
        raise ValueError("Panel no encontrado")

    if inversor is None:
        raise ValueError("Inversor no definido")

    modo = datos.get("modo_dimensionado", "consumo")

    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo=modo,
        n_paneles_total=datos.get("n_paneles"),
        t_min_c=getattr(sizing, "t_min_c", 25.0),
        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
        dos_aguas=getattr(sizing, "dos_aguas", False),
        objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
        pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
        n_inversores=getattr(sizing, "n_inversores", 1),
    )


# ==========================================================
# BUILDER MULTIZONA (🔥 NUEVO)
# ==========================================================
def construir_entrada_panel_desde_zona(z, sizing, catalogos) -> EntradaPaneles:
    """
    Construye EntradaPaneles para una zona individual.

    ✔ No calcula nada
    ✔ Solo define el problema eléctrico
    ✔ Compatible 100% con tu motor actual
    """

    panel: PanelSpec = catalogos.obtener_panel(z.panel_id)
    inversor: InversorSpec = catalogos.obtener_inversor(sizing.inversor_id)

    if panel is None:
        raise ValueError(f"Panel no encontrado: {z.panel_id}")

    if inversor is None:
        raise ValueError("Inversor no definido en sizing")

    # -------------------------
    # BASE COMÚN
    # -------------------------
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

        if z.area_m2 is None:
            raise ValueError(f"Zona {z.nombre} sin área")

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
            raise ValueError(f"Zona {z.nombre} sin paneles definidos")

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
