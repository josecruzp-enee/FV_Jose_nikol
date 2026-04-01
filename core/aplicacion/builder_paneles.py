from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos.catalogos import get_panel, get_inversor


# ==========================================================
# HELPERS
# ==========================================================

def _extraer_ids_equipos(equipos):
    """
    Soporta dict y objeto
    """

    if isinstance(equipos, dict):
        panel_id = equipos.get("panel_id")
        inversor_id = equipos.get("inversor_id")
    else:
        panel_id = getattr(equipos, "panel_id", None)
        inversor_id = getattr(equipos, "inversor_id", None)

    if not panel_id:
        raise ValueError("panel_id no definido en datos.equipos")

    if not inversor_id:
        raise ValueError("inversor_id no definido en datos.equipos")

    return panel_id, inversor_id


def _resolver_catalogos(panel_id, inversor_id):
    panel = get_panel(panel_id)
    inversor = get_inversor(inversor_id)

    if panel is None:
        raise ValueError(f"Panel no encontrado: {panel_id}")

    if inversor is None:
        raise ValueError(f"Inversor no encontrado: {inversor_id}")

    return panel, inversor


def _validar_sistema_fv(datos):
    if not hasattr(datos, "sistema_fv") or not isinstance(datos.sistema_fv, dict):
        raise ValueError("datos.sistema_fv no definido o inválido")

    return datos.sistema_fv


def _build_multizona(sf, panel, inversor, sizing):

    zonas = sf.get("zonas", [])

    if not isinstance(zonas, list) or not zonas:
        raise ValueError("zonas inválidas en sistema_fv")

    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo="multizona",
        n_paneles_total=None,
        zonas=zonas,
        t_min_c=getattr(sizing, "t_min_c", 25.0),
        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
        dos_aguas=getattr(sizing, "dos_aguas", False),
        objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
        pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
        n_inversores=getattr(sizing, "n_inversores", 1),
    )


def _build_normal(sf, panel, inversor, sizing):

    modo = str(sf.get("modo")).strip().lower()
    valor = sf.get("valor")

    if valor is None or float(valor) <= 0:
        raise ValueError(f"Valor inválido en sistema_fv: {sf}")

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


# ==========================================================
# MAIN
# ==========================================================

def construir_entrada_paneles(datos, sizing) -> EntradaPaneles:
    """
    BUILDER ROBUSTO

    ✔ Soporta dict y objeto en equipos
    ✔ Mantiene contrato actual
    ✔ Refactor limpio
    """

    # ==========================================================
    # EQUIPOS
    # ==========================================================
    if not hasattr(datos, "equipos") or datos.equipos is None:
        raise ValueError("datos.equipos no definido")

    panel_id, inversor_id = _extraer_ids_equipos(datos.equipos)

    panel, inversor = _resolver_catalogos(panel_id, inversor_id)

    # ==========================================================
    # SISTEMA FV
    # ==========================================================
    sf = _validar_sistema_fv(datos)

    # ==========================================================
    # MULTIZONA
    # ==========================================================
    if sf.get("modo") == "multizona" or sf.get("zonas"):
        return _build_multizona(sf, panel, inversor, sizing)

    # ==========================================================
    # NORMAL
    # ==========================================================
    if sf.get("modo"):
        return _build_normal(sf, panel, inversor, sizing)

    raise ValueError("sistema_fv sin modo válido")
