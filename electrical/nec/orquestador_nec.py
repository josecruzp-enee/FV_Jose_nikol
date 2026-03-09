from typing import Dict, Any
import math

from core.dominio.contrato import ResultadoSizing
from electrical.paquete_nec import armar_paquete_nec


def ejecutar_nec(
    p,
    sizing: ResultadoSizing,
    strings: Dict[str, Any],
) -> Dict[str, Any]:

    ee: Dict[str, Any] = {}

    # ------------------------------------------------------
    # 1. Base eléctrica del proyecto (definida por proyectista)
    # ------------------------------------------------------

    base = getattr(p, "electrico", None)

    vac_ll = None
    fases = 1
    fp = 1.0

    if isinstance(base, dict):

        vac_ll = base.get("vac")
        fases = base.get("fases", 1)
        fp = base.get("fp", 1.0)

        if vac_ll:
            ee["vac_ll"] = vac_ll

            if fases == 3:
                ee["vac_ln"] = vac_ll / math.sqrt(3)
            else:
                ee["vac_ln"] = vac_ll

    ee["fases"] = fases
    ee["fp"] = fp

    # ------------------------------------------------------
    # 2. Potencias desde sizing
    # ------------------------------------------------------

    pdc_w = float(sizing.pdc_kw) * 1000
    pac_w = float(sizing.pac_kw) * 1000

    ee["potencia_dc_w"] = pdc_w
    ee["potencia_ac_w"] = pac_w

    # ------------------------------------------------------
    # 3. Corriente AC nominal del inversor
    # ------------------------------------------------------

    if vac_ll and vac_ll > 0:

        if fases == 3:
            iac_nom = pac_w / (math.sqrt(3) * vac_ll * fp)
        else:
            iac_nom = pac_w / (vac_ll * fp)

        ee["iac_nom_a"] = iac_nom

    # ------------------------------------------------------
    # 4. Datos desde strings
    # ------------------------------------------------------

    if strings:

        rec = strings.get("recomendacion", {})
        lista = strings.get("strings", [])

        vmp_string = float(rec.get("vmp_string_v", 0))

        if vmp_string > 0:
            ee["vdc_nom"] = vmp_string

        # corriente DC nominal
        idesign = max(
            (float(st.get("idesign_cont_a", 0)) for st in lista),
            default=0,
        )

        if idesign > 0:
            ee["idc_nom"] = idesign

        # ----------------------------------------------
        # Datos necesarios para cálculo de corrientes
        # ----------------------------------------------

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
                "v_ac_nom_v": vac_ll,
                "fases": fases,
                "fp": fp,
                "iac_nom_a": ee.get("iac_nom_a"),
            }

    # ------------------------------------------------------
    # 5. Garantizar voltaje DC mínimo
    # ------------------------------------------------------

    if "vdc_nom" not in ee:
        ee["vdc_nom"] = 600

    # ------------------------------------------------------
    # 6. Construcción paquete NEC
    # ------------------------------------------------------

    paquete = armar_paquete_nec(ee)

    return {
        "ok": True,
        "input": ee,
        "paq": paquete,
    }
