from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos.catalogos import get_panel, get_inversor


def construir_entrada_paneles(datos, sizing) -> EntradaPaneles:
    """
    ✔ SOLO dataclasses
    ✔ SIN legacy
    ✔ FUENTE ÚNICA DE VERDAD
    ✔ MODO CORRECTAMENTE MAPEADO (UI → MOTOR)
    """

    # ==========================================================
    # EQUIPOS (OBLIGATORIO)
    # ==========================================================
    if not hasattr(datos, "equipos") or datos.equipos is None:
        raise ValueError("datos.equipos no definido")

    equipos = datos.equipos

    panel_id = getattr(equipos, "panel_id", None)
    inversor_id = getattr(equipos, "inversor_id", None)

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
    # SISTEMA FV (OBLIGATORIO)
    # ==========================================================
    if not hasattr(datos, "sistema_fv") or not isinstance(datos.sistema_fv, dict):
        raise ValueError("datos.sistema_fv no definido o inválido")

    sf = datos.sistema_fv

    modo_diseno = sf.get("modo_diseno")

    if not modo_diseno:
        raise ValueError("modo_diseno no definido en sistema_fv")

    modo_diseno = str(modo_diseno).strip().lower()

    # ==========================================================
    # MAPEO DE MODO (UI → MOTOR)
    # ==========================================================
    if modo_diseno == "zonas":
        modo = "multizona"

    elif modo_diseno == "manual":
        modo = "manual"

    elif modo_diseno == "auto":
        sizing_input = sf.get("sizing_input", {})

        if not isinstance(sizing_input, dict):
            raise ValueError("sizing_input inválido")

        modo = sizing_input.get("modo")

        if not modo:
            raise ValueError("modo no definido en sizing_input")

        modo = str(modo).strip().lower()

    else:
        raise ValueError(f"modo_diseno inválido: {modo_diseno}")

    # ==========================================================
    # SALIDA
    # ==========================================================
    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo=modo,
        n_paneles_total=getattr(sizing, "n_paneles", None),
        t_min_c=getattr(sizing, "t_min_c", 25.0),
        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
        dos_aguas=getattr(sizing, "dos_aguas", False),
        objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
        pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
        n_inversores=getattr(sizing, "n_inversores", 1),
    )
