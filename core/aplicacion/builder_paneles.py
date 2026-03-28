from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos.catalogos import get_panel, get_inversor


def construir_entrada_paneles(datos, sizing) -> EntradaPaneles:
    """
    BUILDER ROBUSTO

    ✔ Acepta formato UI actual (modo + valor)
    ✔ Acepta formato nuevo (modo_diseno + sizing_input)
    ✔ Acepta multizona
    ✔ Normaliza todo hacia el motor
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

    # ==========================================================
    # 🔥 NORMALIZACIÓN CENTRAL
    # ==========================================================
    modo = None

    # ----------------------------------------------------------
    # CASO 1: MULTIZONA (UI)
    # ----------------------------------------------------------
    if sf.get("modo") == "multizona" or sf.get("zonas"):

        modo = "multizona"

        zonas = sf.get("zonas", [])

        if not isinstance(zonas, list) or not zonas:
            raise ValueError("zonas inválidas en sistema_fv")

        for i, z in enumerate(zonas):
            if not isinstance(z, dict):
                raise ValueError(f"Zona {i+1} inválida")

            if "n_paneles" in z:
                if int(z["n_paneles"]) <= 0:
                    raise ValueError(f"Zona {i+1}: n_paneles inválido")
            elif "area" in z:
                if float(z["area"]) <= 0:
                    raise ValueError(f"Zona {i+1}: área inválida")
            else:
                raise ValueError(f"Zona {i+1}: sin datos válidos")

    # ----------------------------------------------------------
    # CASO 2: FORMATO NUEVO
    # ----------------------------------------------------------
    elif sf.get("modo_diseno"):

        modo_diseno = str(sf.get("modo_diseno")).strip().lower()

        if modo_diseno == "zonas":
            modo = "multizona"

        elif modo_diseno == "manual":
            modo = "manual"

        elif modo_diseno in ["auto", "automatico", "automático"]:

            sizing_input = sf.get("sizing_input", {})

            if not isinstance(sizing_input, dict):
                raise ValueError("sizing_input inválido")

            modo = sizing_input.get("modo")

            if not modo:
                raise ValueError("modo no definido en sizing_input")

            modo = str(modo).strip().lower()

        else:
            raise ValueError(f"modo_diseno inválido: {modo_diseno}")

    # ----------------------------------------------------------
    # CASO 3: FORMATO UI ACTUAL
    # ----------------------------------------------------------
    elif sf.get("modo"):

        modo = str(sf.get("modo")).strip().lower()

        if modo == "multizona":
            raise ValueError("multizona sin zonas definidas")

        valor = sf.get("valor")

        if valor is None or float(valor) <= 0:
            raise ValueError(f"Valor inválido en sistema_fv: {sf}")

    # ----------------------------------------------------------
    # ERROR TOTAL
    # ----------------------------------------------------------
    else:
        raise ValueError("sistema_fv sin modo válido")

    # ==========================================================
    # SALIDA
    # ==========================================================
    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo=modo,
        n_paneles_total=getattr(sizing, "n_paneles", None),
        zonas=zonas if modo == "multizona" else None,
        t_min_c=getattr(sizing, "t_min_c", 25.0),
        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
        dos_aguas=getattr(sizing, "dos_aguas", False),
        objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
        pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
        n_inversores=getattr(sizing, "n_inversores", 1),
    )
