from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.catalogos.catalogos import get_panel, get_inversor


# ==========================================================
# HELPERS
# ==========================================================

def _extraer_ids_equipos(equipos):

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


# ==========================================================
# NORMALIZACIÓN CORRECTA (🔥 FIX REAL)
# ==========================================================

def _normalizar_zonas(zonas):

    def estimar_paneles(area):
        if area is None or area <= 0:
            return 1
        return max(int(area / 2.0), 1)

    out = []

    for z in zonas:
        if not isinstance(z, dict):
            continue

        n = z.get("n_paneles")

        if n is None:
            n = estimar_paneles(z.get("area"))

        if n <= 0:
            n = 1

        out.append({"n_paneles": n})

    return out
# ==========================================================
# BUILD MULTIZONA
# ==========================================================

def _build_multizona(sf, panel, inversor, sizing):

    zonas_raw = sf.get("zonas", [])

    if not isinstance(zonas_raw, list) or not zonas_raw:
        raise ValueError("zonas inválidas en sistema_fv")

    zonas_norm = _normalizar_zonas(zonas_raw)

    # 🔥 CONVERSIÓN A TIPADO FUERTE
    zonas_obj = [
        ZonaFV(n_paneles=z["n_paneles"])
        for z in zonas_norm
    ]

    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo="multizona",
        n_paneles_total=None,
        zonas=zonas_obj,
        t_min_c=getattr(sizing, "t_min_c", 25.0),
        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
        dos_aguas=getattr(sizing, "dos_aguas", False),
        objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
        pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
        n_inversores=getattr(sizing, "n_inversores", 1),
    )
# ==========================================================
# BUILD NORMAL
# ==========================================================

def _build_normal(sf, panel, inversor, sizing):

    modo = str(sf.get("modo")).strip().lower()
    valor = sf.get("valor")

    if valor is None or float(valor) <= 0:
        raise ValueError(f"Valor inválido en sistema_fv: {sf}")

    n_paneles_total = getattr(sizing, "n_paneles", None)

    if n_paneles_total is None and sf.get("zonas"):
        zonas = _normalizar_zonas(sf.get("zonas", []))
        n_paneles_total = sum(z["n_paneles"] for z in zonas)

    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo=modo,
        n_paneles_total=n_paneles_total,
        zonas=None,
        t_min_c=getattr(sizing, "t_min_c", 25.0),
        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
        dos_aguas=getattr(sizing, "dos_aguas", False),
        objetivo_dc_ac=getattr(sizing, "dc_ac_ratio", None),
        pdc_kw_objetivo=getattr(sizing, "pdc_kw", None),
        n_inversores=getattr(sizing, "n_inversores", 1),
    )


# ==========================================================
# MAIN BUILDER
# ==========================================================

def construir_entrada_paneles(datos, sizing) -> EntradaPaneles:

    if not hasattr(datos, "equipos") or datos.equipos is None:
        raise ValueError("datos.equipos no definido")

    panel_id, inversor_id = _extraer_ids_equipos(datos.equipos)
    panel, inversor = _resolver_catalogos(panel_id, inversor_id)

    sf = _validar_sistema_fv(datos)

    # 🔥 MULTIZONA PRIORIDAD
    if sf.get("modo") == "multizona" or sf.get("zonas"):
        return _build_multizona(sf, panel, inversor, sizing)

    # 🔹 NORMAL
    if sf.get("modo"):
        return _build_normal(sf, panel, inversor, sizing)

    raise ValueError("sistema_fv sin modo válido")
