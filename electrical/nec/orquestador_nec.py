# electrical/nec/orquestador_nec.py

from typing import Dict, Any
from core.dominio.contrato import ResultadoSizing
from electrical.paquete_nec import armar_paquete_nec


def ejecutar_nec(
    p: Any,
    sizing: ResultadoSizing,   # ← YA NO Dict
    strings: Dict[str, Any],
) -> Dict[str, Any]:

    ee: Dict[str, Any] = {}

    # Base eléctrica desde datos
    base = getattr(p, "electrico", {}) or {}
    if isinstance(base, dict):
        ee.update(base)

        ee["vac_ll"] = base.get("vac")
        ee["vac_ln"] = base.get("vac")
        ee["fases"] = base.get("fases")
        ee["fp"] = base.get("fp")

    # 🔒 Potencias desde contrato fuerte
    ee["potencia_dc_kw"] = float(sizing.pdc_kw)
    ee["potencia_ac_kw"] = float(sizing.pac_kw)

    # Información desde strings
    if strings.get("ok"):
        rec = strings.get("recomendacion", {}) or {}

        vmp_string = float(rec.get("vmp_string_v", 0.0))
        if vmp_string > 0:
            ee["vdc_nom"] = vmp_string

        idesign = 0.0
        for st in strings.get("strings", []) or []:
            idesign = max(idesign, float(st.get("idesign_cont_a", 0.0)))

        if idesign > 0:
            ee["idc_nom"] = idesign

    paq = armar_paquete_nec(ee)

    return {
        "ok": True,
        "input": ee,
        "paq": paq,
    }
