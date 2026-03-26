from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos.catalogos import get_panel, get_inversor


def construir_entrada_paneles(datos, sizing) -> EntradaPaneles:
    """
    ✔ Solo dataclasses
    ✔ Sin ambigüedad
    ✔ Fuente única: datos.equipos
    """

    # ==========================================================
    # EQUIPOS
    # ==========================================================
    if not hasattr(datos, "equipos") or datos.equipos is None:
        raise ValueError("datos.equipos no definido")

    equipos = datos.equipos

    panel_id = getattr(equipos, "panel_id", None)
    inversor_id = getattr(equipos, "inversor_id", None)

    # ==========================================================
    # VALIDACIONES
    # ==========================================================
    if not panel_id:
        raise ValueError("panel_id no definido en datos.equipos")

    if not inversor_id:
        raise ValueError("inversor_id no definido en datos.equipos")

    # ==========================================================
    # CATÁLOGOS
    # ==========================================================
    panel = get_panel(panel_id)
    inversor = get_inversor(inversor_id)

    if panel is None:
        raise ValueError(f"Panel no encontrado: {panel_id}")

    if inversor is None:
        raise ValueError(f"Inversor no encontrado: {inversor_id}")

    # ==========================================================
    # MODO (normalizado)
    # ==========================================================
    modo = str(datos.modo_dimensionado).strip().lower()

    # ==========================================================
    # SALIDA
    # ==========================================================
    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo=modo,
        n_paneles_total=getattr(datos, "n_paneles", None),
        t_min_c=getattr(sizing, "t_min_c", 25.0),
        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
        dos_aguas=getattr(sizing, "dos_aguas", False),
        objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
        pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
        n_inversores=getattr(sizing, "n_inversores", 1),
    )
