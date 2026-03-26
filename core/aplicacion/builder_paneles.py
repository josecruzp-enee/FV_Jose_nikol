def construir_entrada_paneles(datos, sizing) -> EntradaPaneles:
    """
    ✔ Solo dataclasses
    ✔ Sin ambigüedad
    ✔ Sin dict
    """

    equipos = datos.equipos

    panel_id = equipos.panel_id
    inversor_id = equipos.inversor_id

    if not panel_id:
        raise ValueError("panel_id no definido")

    if not inversor_id:
        raise ValueError("inversor_id no definido")

    panel = get_panel(panel_id)
    inversor = get_inversor(inversor_id)

    if panel is None:
        raise ValueError(f"Panel no encontrado: {panel_id}")

    if inversor is None:
        raise ValueError(f"Inversor no encontrado: {inversor_id}")

    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo=datos.modo_dimensionado,
        n_paneles_total=datos.n_paneles,
        t_min_c=sizing.t_min_c,
        t_oper_c=sizing.t_oper_c,
        dos_aguas=sizing.dos_aguas,
        objetivo_dc_ac=sizing.dc_ac_ratio,
        pdc_kw_objetivo=sizing.pdc_kw,
        n_inversores=sizing.n_inversores,
    )
