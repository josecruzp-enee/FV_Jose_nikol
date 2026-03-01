from electrical.catalogos import get_inversor, ids_inversores
from electrical.inversor.sizing_inversor import SizingInput, ejecutar_sizing


def ejecutar_inversor_desde_sizing(
    *,
    consumo_anual_kwh: float,
    prod_anual_por_kwp_kwh: float,
    cobertura_obj: float,
    dc_ac_obj: float,
    panel_w: float,
    pdc_kw: float,
    inversor_id_forzado: Optional[str] = None,
) -> Dict[str, Any]:

    inp = SizingInput(
        consumo_anual_kwh=consumo_anual_kwh,
        produccion_anual_por_kwp_kwh=prod_anual_por_kwp_kwh,
        cobertura_obj=cobertura_obj,
        dc_ac_obj=dc_ac_obj,
        pmax_panel_w=panel_w,
        pdc_obj_kw=pdc_kw,
    )

    resultado = ejecutar_sizing(
        inp=inp,
        inversores_catalogo=[get_inversor(i) for i in ids_inversores()],
    )

    inv_id_rec = resultado.get("inversor_recomendado")
    inv_id_final = inversor_id_forzado or inv_id_rec

    if not inv_id_final:
        raise ValueError("No se pudo determinar inversor recomendado")

    inv = get_inversor(inv_id_final)

    pac_kw = float(inv.kw_ac)
    if pac_kw <= 0:
        raise ValueError("Potencia AC inválida en inversor")

    return {
        "inversor_id": inv_id_final,
        "pac_kw": pac_kw,
        "meta": resultado.get("inversor_recomendado_meta", {}),
    }
