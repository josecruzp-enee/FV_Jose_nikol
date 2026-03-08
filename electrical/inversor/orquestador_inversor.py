from __future__ import annotations
from typing import Dict, Any, Optional
from math import ceil
from electrical.catalogos import get_inversor, ids_inversores

def ejecutar_inversor_desde_sizing(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    inversor_id_forzado: Optional[str] = None,
) -> Dict[str, Any]:

    if pdc_kw <= 0:
        raise ValueError("pdc_kw inválido")

    if dc_ac_obj <= 0:
        raise ValueError("dc_ac_obj inválido")

    pac_obj_kw = pdc_kw / dc_ac_obj

    # -----------------------------
    # inversor forzado
    # -----------------------------
    if inversor_id_forzado:

        inv = get_inversor(inversor_id_forzado)

        if inv is None:
            raise ValueError("Inversor forzado no encontrado")

        pac = float(inv.kw_ac)

        n_inv = ceil(pac_obj_kw / pac)

        return {
            "inversor_id": inversor_id_forzado,
            "pac_kw": pac,
            "n_inversores": n_inv,
            "pac_total_kw": pac * n_inv,
            "pac_obj_kw": pac_obj_kw,
        }

    # -----------------------------
    # selección automática
    # -----------------------------
    mejor = None
    mejor_n = None
    mejor_pac = None

    for iid in ids_inversores():

        inv = get_inversor(iid)

        pac = float(inv.kw_ac)

        n_inv = ceil(pac_obj_kw / pac)

        pac_total = n_inv * pac

        # buscamos la solución con menor potencia total instalada
        if mejor is None or pac_total < mejor:

            mejor = pac_total
            mejor_n = n_inv
            mejor_pac = pac
            mejor_id = iid

    return {
        "inversor_id": mejor_id,
        "pac_kw": mejor_pac,
        "n_inversores": mejor_n,
        "pac_total_kw": mejor,
        "pac_obj_kw": pac_obj_kw,
    }
