from __future__ import annotations

from electrical.paneles.entrada_panel import EntradaPaneles, ZonaFV
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
# MAPEO UI → MOTOR
# ==========================================================

def _mapear_modo_ui_a_paneles(modo_ui: str):

    modo_ui = str(modo_ui).strip().lower()

    if modo_ui == "paneles":
        return "manual"

    if modo_ui in ["cobertura", "potencia", "consumo", "kw_objetivo"]:
        return "consumo"   # 🔥 automático

    if modo_ui == "area":
        return "area"

    raise ValueError(f"Modo no soportado: {modo_ui}")
# ==========================================================
# NORMALIZACIÓN ZONAS
# ==========================================================

def _normalizar_zonas(zonas):

    def estimar_paneles(area):
        if area is None or area <= 0:
            return 1
        return max(int(area / 2.0), 1)

    out = []

    for i, z in enumerate(zonas):

        if not isinstance(z, dict):
            continue

        modo_z = z.get("modo")

        if not modo_z:
            raise ValueError(f"Zona {i+1} sin modo")

        modo_z = modo_z.lower()

        if modo_z not in ["paneles", "area"]:
            raise ValueError(f"Zona {i+1}: modo inválido ({modo_z})")

        n = z.get("n_paneles")
        area = z.get("area")

        if modo_z == "paneles":
            if n is None or n <= 0:
                raise ValueError(f"Zona {i+1}: n_paneles inválido")

        if modo_z == "area":
            if area is None or area <= 0:
                raise ValueError(f"Zona {i+1}: área inválida")
            n = estimar_paneles(area)

        out.append({
            "modo": modo_z,
            "n_paneles": int(n),
            "azimut": z.get("azimut"),
            "inclinacion": z.get("inclinacion"),
        })

    return out


# ==========================================================
# BUILD MULTIZONA
# ==========================================================

def _build_multizona(sf, panel, inversor, sizing):

    zonas_raw = sf.get("zonas", [])

    if not isinstance(zonas_raw, list) or not zonas_raw:
        raise ValueError("multizona sin zonas válidas")

    zonas_norm = _normalizar_zonas(zonas_raw)

    zonas_obj = [
        ZonaFV(
            n_paneles=z["n_paneles"],
            azimut=z.get("azimut"),
            inclinacion=z.get("inclinacion"),
        )
        for z in zonas_norm
    ]

    return EntradaPaneles(
        panel=panel,
        inversor=inversor,
        modo="manual",
        zonas=zonas_obj,

        n_paneles_total=None,

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

    modo_ui = sf.get("modo")
    valor = sf.get("valor")

    modo = _mapear_modo_ui_a_paneles(modo_ui)

    # ==================================================
    # PRIORIDAD: UI > sizing
    # ==================================================
    n_paneles_total = None

    if modo_ui == "paneles":
        if valor is None or int(valor) <= 0:
            raise ValueError("Valor inválido para modo paneles")
        n_paneles_total = int(valor)

    elif modo_ui in ["cobertura", "potencia"]:
        n_paneles_total = getattr(sizing, "n_paneles", None)

    elif modo_ui == "area":
        # paneles se calcularán internamente
        n_paneles_total = None

    if modo == "paneles" and (n_paneles_total is None or n_paneles_total <= 0):
        raise ValueError("No se pudo determinar n_paneles_total")

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

    modo = sf.get("modo")

    if not modo:
        raise ValueError("sistema_fv sin modo")

    modo = modo.lower()

    # ==================================================
    # MULTIZONA
    # ==================================================
    if modo == "multizona":
        return _build_multizona(sf, panel, inversor, sizing)

    # ==================================================
    # NORMAL (auto + manual simple)
    # ==================================================
    return _build_normal(sf, panel, inversor, sizing)
