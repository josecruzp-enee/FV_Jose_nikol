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

    ee["potencia_dc_w"] = float(sizing.pdc_kw) * 1000
    ee["potencia_ac_w"] = float(sizing.pac_kw) * 1000

    # -------------------------
    # Datos desde strings
    # -------------------------

    if strings:

        rec = strings.get("recomendacion", {})
        lista = strings.get("strings", [])

        vmp_string = float(rec.get("vmp_string_v", 0))

        if vmp_string > 0:
            ee["vdc_nom"] = vmp_string

        # corriente de diseño máxima
        idesign = max(
            (float(st.get("idesign_cont_a", 0)) for st in lista),
            default=0,
        )

        if idesign > 0:
            ee["idc_nom"] = idesign

        # =====================================
        # DATOS NECESARIOS PARA MOTOR CORRIENTES
        # =====================================

        if lista:

            s0 = lista[0]

            ee["strings"] = {
                "corrientes_input": {
                    "imp_string_a": float(s0.get("imp_a", 0)),
                     "isc_string_a": float(s0.get("isc_a", 0)),
                     "strings_por_mppt": int(s0.get("n_paralelo", 1)),
                     "n_strings_total": int(rec.get("n_strings_total", 0)),
                }
            }

            ee["inversor"] = {
                "kw_ac": float(sizing.pac_kw),
                "v_ac_nom_v": ee.get("vac_ll", 480),
                "fases": ee.get("fases", 3),
                "fp": ee.get("fp", 1.0),
            }

    # -------------------------
    # Garantizar voltaje DC mínimo
    # -------------------------

    if "vdc_nom" not in ee:
        ee["vdc_nom"] = 600

    # -------------------------
    # Construcción paquete NEC
    # -------------------------

    paquete = armar_paquete_nec(ee)

    return {
        "ok": True,
        "input": ee,
        "paq": paquete,
    }
