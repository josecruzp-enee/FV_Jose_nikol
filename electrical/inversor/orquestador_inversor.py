from __future__ import annotations
from typing import Dict, Any, Optional

from electrical.catalogos import get_inversor, ids_inversores


# ==========================================================
# API pública — Selección por potencia DC
# ==========================================================

def ejecutar_inversor_desde_sizing(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    inversor_id_forzado: Optional[str] = None,
) -> Dict[str, Any]:

    if pdc_kw <= 0:
        raise ValueError("pdc_kw inválido para selección de inversor")

    if dc_ac_obj <= 0:
        raise ValueError("dc_ac_obj inválido")

    # ------------------------------------------------------
    # Potencia AC objetivo
    # ------------------------------------------------------
    pac_obj_kw = pdc_kw / dc_ac_obj

    # ------------------------------------------------------
    # Si hay inversor forzado
    # ------------------------------------------------------
    if inversor_id_forzado:
        inv = get_inversor(inversor_id_forzado)
        if inv is None:
            raise ValueError("Inversor forzado no encontrado")

        return {
            "inversor_id": inversor_id_forzado,
            "pac_kw": float(inv.kw_ac),
            "pac_obj_kw": pac_obj_kw,
        }

    # ------------------------------------------------------
    # Selección automática
    # ------------------------------------------------------
    mejor_id = None
    mejor_pac = None

    for iid in ids_inversores():
        inv = get_inversor(iid)
        pac = float(inv.kw_ac)

        # buscamos el más cercano >= pac_obj
        if pac >= pac_obj_kw:
            if mejor_pac is None or pac < mejor_pac:
                mejor_id = iid
                mejor_pac = pac

    # Si ninguno cumple >= objetivo, tomar el mayor disponible
    if mejor_id is None:
        max_pac = -1.0
        for iid in ids_inversores():
            inv = get_inversor(iid)
            pac = float(inv.kw_ac)
            if pac > max_pac:
                max_pac = pac
                mejor_id = iid
                mejor_pac = pac

    if mejor_id is None:
        raise ValueError("No hay inversores disponibles en catálogo")

    return {
        "inversor_id": mejor_id,
        "pac_kw": float(mejor_pac),
        "pac_obj_kw": pac_obj_kw,
    }
