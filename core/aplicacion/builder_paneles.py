def construir_entrada_paneles(datos: Any, sizing, catalogos=None) -> EntradaPaneles:
    """
    Construcción clásica (una sola zona).

    ✔ Fuente única de equipos: datos.equipos
    ✔ Validación obligatoria
    ✔ No depende de sizing para equipos
    """

    # ==========================================================
    # EXTRAER EQUIPOS
    # ==========================================================
    equipos = getattr(datos, "equipos", {}) or {}

    panel_id = equipos.get("panel_id")
    inversor_id = equipos.get("inversor_id")

    # ==========================================================
    # VALIDACIONES (CRÍTICO)
    # ==========================================================
    if not panel_id:
        raise ValueError(
            "panel_id no definido en datos.equipos "
            "(UI → seleccion_equipos.py)"
        )

    if not inversor_id:
        raise ValueError(
            "inversor_id no definido en datos.equipos "
            "(UI → seleccion_equipos.py)"
        )

    # ==========================================================
    # OBTENER MODELOS
    # ==========================================================
    panel: PanelSpec = get_panel(panel_id)
    inversor: InversorSpec = get_inversor(inversor_id)

    if panel is None:
        raise ValueError(f"Panel no encontrado en catálogo: {panel_id}")

    if inversor is None:
        raise ValueError(f"Inversor no encontrado en catálogo: {inversor_id}")

    # ==========================================================
    # MODO
    # ==========================================================
    modo = getattr(datos, "modo_dimensionado", "consumo")

    # ==========================================================
    # CONSTRUIR ENTRADA
    # ==========================================================
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
