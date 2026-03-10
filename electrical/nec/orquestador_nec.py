from typing import Dict, Any
import math

from core.dominio.contrato import ResultadoSizing
from electrical.paquete_nec import armar_paquete_nec


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

    if isinstance(p, dict):
        base = p.get("electrico", {})
    else:
        base = getattr(p, "electrico", {})

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
    kw_ac = float(sizing.kw_ac)

    ee["potencia_dc_w"] = pdc_w
    ee["potencia_ac_w"] = kw_ac * 1000

    # ------------------------------------------------------
    # 3. Datos desde strings
    # ------------------------------------------------------

    if not strings:
        raise ValueError("NEC requiere datos del módulo strings")

    rec = strings.get("recomendacion", {})
    lista = strings.get("strings", [])

    # ------------------------------------------------------
    # Voltaje DC desde strings
    # ------------------------------------------------------

    vmp_string = float(rec.get("vmp_string_v", 0))

    if vmp_string <= 0:
        raise ValueError("vmp_string_v no definido en resultado strings")

    ee["vdc_nom"] = vmp_string

    # ------------------------------------------------------
    # Corriente DC nominal (desde strings)
    # ------------------------------------------------------

    idesign = max(
        (float(st.get("idesign_cont_a", 0)) for st in lista),
        default=0,
    )

    if idesign > 0:
        ee["idc_nom"] = idesign

    # ------------------------------------------------------
    # Datos para motor de corrientes
    # ------------------------------------------------------

    if lista:

        s0 = lista[0]

        ee["strings"] = {
            "corrientes_input": {

                "imp_string_a": float(s0.get("imp_string_a", 0)),
                "isc_string_a": float(s0.get("isc_string_a", 0)),

                "strings_por_mppt": int(s0.get("n_paralelo", 1)),
                "n_strings_total": int(rec.get("n_strings_total", 0)),
            }
        }

        ee["inversor"] = {

            # potencia AC
            "kw_ac": kw_ac,

            # datos eléctricos
            "v_ac_nom_v": vac_ll,
            "fases": fases,
            "fp": fp,

            # topología inversor
            "mppt": int(s0.get("mppt", 2)),
        }

    # ------------------------------------------------------
    # 4. Construcción paquete NEC
    # ------------------------------------------------------

    paquete = armar_paquete_nec(ee)

    return {
        "ok": True,
        "input": ee,
        "paq": paquete,
    }
