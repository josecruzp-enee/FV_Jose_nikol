from typing import Dict, Any
from core.dominio.contrato import ResultadoSizing
from electrical.paquete_nec import armar_paquete_nec


def ejecutar_nec(
    p,
    sizing: ResultadoSizing,
    strings: Dict[str, Any],
) -> Dict[str, Any]:

    ee: Dict[str, Any] = {}

    # -------------------------
    # Base eléctrica del proyecto
    # -------------------------

    base = getattr(p, "electrico", None)

    if isinstance(base, dict):

        vac = base.get("vac")

        if vac:
            ee["vac_ll"] = vac

            # calcular LN si es trifásico
            fases = base.get("fases", 1)

            if fases == 3:
                ee["vac_ln"] = vac / 1.732
            else:
                ee["vac_ln"] = vac

        ee["fases"] = base.get("fases")
        ee["fp"] = base.get("fp")

    # -------------------------
    # Potencias desde sizing
    # -------------------------

    ee["potencia_dc_kw"] = float(sizing.pdc_kw)
    ee["potencia_ac_kw"] = float(sizing.pac_kw)

    # -------------------------
    # Datos desde strings
    # -------------------------

    if strings.get("ok"):

        rec = strings.get("recomendacion", {})

        vmp_string = float(rec.get("vmp_string_v", 0))

        if vmp_string > 0:
            ee["vdc_nom"] = vmp_string

        # corriente de diseño máxima
        idesign = max(
            (float(st.get("idesign_cont_a", 0)) for st in strings.get("strings", [])),
            default=0,
        )

        if idesign > 0:
            ee["idc_nom"] = idesign

    # -------------------------
    # Construcción paquete NEC
    # -------------------------

    paquete = armar_paquete_nec(ee)

    return {
        "ok": True,
        "input": ee,
        "paq": paquete,
    }
