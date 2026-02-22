# nucleo/electrico_ref.py  (WRAPPER TEMPORAL)
from __future__ import annotations
from typing import Any, Dict, Optional

from electrical.catalogos.modelos import ParametrosCableado
from electrical.ref.paquete_electrico import calcular_paquete_electrico_ref


def simular_electrico_fv_para_pdf(
    *,
    v_ac: float = 240.0,
    i_ac_estimado: float = 41.7,
    dist_ac_m: float = 25.0,
    objetivo_vdrop_ac_pct: float = 2.0,
    vmp_string_v: float = 410.0,
    imp_a: float = 13.2,
    isc_a: Optional[float] = None,
    dist_dc_m: float = 15.0,
    objetivo_vdrop_dc_pct: float = 2.0,
    incluye_neutro_ac: bool = False,
    otros_ccc_en_misma_tuberia: int = 0,
) -> Dict[str, Any]:
    p = ParametrosCableado(
        vac=float(v_ac),
        dist_dc_m=float(dist_dc_m),
        dist_ac_m=float(dist_ac_m),
        vdrop_obj_dc_pct=float(objetivo_vdrop_dc_pct),
        vdrop_obj_ac_pct=float(objetivo_vdrop_ac_pct),
        incluye_neutro_ac=bool(incluye_neutro_ac),
        otros_ccc=int(otros_ccc_en_misma_tuberia),
    )

    pkg = calcular_paquete_electrico_ref(
        params=p,
        vmp_string_v=float(vmp_string_v),
        imp_a=float(imp_a),
        isc_a=None if isc_a is None else float(isc_a),
        iac_estimado_a=float(i_ac_estimado),
        fases_ac=1,
        cfg_tecnicos=None,
    )
    return pkg
