from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos.catalogos import get_panel, get_inversor


def construir_entrada_paneles(datos, sizing):
    """
    BUILDER CORREGIDO (MULTIZONA REAL)

    ✔ Multizona devuelve LISTA de entradas
    ✔ Manual/Auto devuelve UNA entrada
    ✔ Compatible con todo tu sistema actual
    """

    # ==========================================================
    # EQUIPOS
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

    panel = get_panel(panel_id)
    inversor = get_inversor(inversor_id)

    if panel is None:
        raise ValueError(f"Panel no encontrado: {panel_id}")

    if inversor is None:
        raise ValueError(f"Inversor no encontrado: {inversor_id}")

    # ==========================================================
    # SISTEMA FV
    # ==========================================================
    if not hasattr(datos, "sistema_fv") or not isinstance(datos.sistema_fv, dict):
        raise ValueError("datos.sistema_fv no definido o inválido")

    sf = datos.sistema_fv

    modo = None
    zonas = []

    # ==========================================================
    # 🔥 CASO MULTIZONA
    # ==========================================================
    if sf.get("modo") == "multizona" or sf.get("zonas"):

        modo = "multizona"
        zonas = sf.get("zonas", [])

        if not isinstance(zonas, list) or not zonas:
            raise ValueError("zonas inválidas en sistema_fv")

        entradas = []

        for i, z in enumerate(zonas, 1):

            if not isinstance(z, dict):
                raise ValueError(f"Zona {i} inválida")

            if "n_paneles" not in z:
                raise ValueError(f"Zona {i}: falta n_paneles")

            n_paneles = int(z.get("n_paneles") or 0)

            if n_paneles <= 0:
                raise ValueError(f"Zona {i}: n_paneles inválido")

            # 🔥 cada zona = una entrada independiente
            entradas.append(
                EntradaPaneles(
                    panel=panel,
                    inversor=inversor,
                    modo="manual",
                    n_paneles_total=n_paneles,
                    zonas=None,
                    t_min_c=getattr(sizing, "t_min_c", 25.0),
                    t_oper_c=getattr(sizing, "t_oper_c", 55.0),
                    dos_aguas=getattr(sizing, "dos_aguas", False),
                    objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
                    pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
                    n_inversores=getattr(sizing, "n_inversores", 1),
                )
            )

        return entradas  # 🔥 CLAVE: lista

    # ==========================================================
    # CASO NO MULTIZONA (MANUAL / AUTO)
    # ==========================================================
    if sf.get("modo"):
        modo = str(sf.get("modo")).strip().lower()

        if modo == "multizona":
            raise ValueError("multizona sin zonas definidas")

        valor = sf.get("valor")

        if valor is None or float(valor) <= 0:
            raise ValueError(f"Valor inválido en sistema_fv: {sf}")

    else:
        raise ValueError("sistema_fv sin modo válido")

    # ==========================================================
    # SALIDA NORMAL
    # ==========================================================
    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo=modo,
        n_paneles_total=getattr(sizing, "n_paneles", None),
        zonas=None,
        t_min_c=getattr(sizing, "t_min_c", 25.0),
        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
        dos_aguas=getattr(sizing, "dos_aguas", False),
        objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
        pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
        n_inversores=getattr(sizing, "n_inversores", 1),
    )
