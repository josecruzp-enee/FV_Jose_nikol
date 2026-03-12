from typing import Dict, Any
import math

from core.dominio.contrato import ResultadoSizing
from electrical.paquete_nec import armar_paquete_nec
from electrical.circuitos.generador_circuitos_dc import generar_circuitos_dc


def ejecutar_nec(
    p,
    sizing: ResultadoSizing,
    strings: Dict[str, Any],
) -> Dict[str, Any]:

    ee: Dict[str, Any] = {}

    # ------------------------------------------------------
    # 1. Base eléctrica del proyecto
    # ------------------------------------------------------

    if isinstance(p, dict):
        base = p.get("electrico", {})
    else:
        base = getattr(p, "electrico", {})

    vac_ll = None
    fases = 1
    fp = 1.0

    if isinstance(base, dict):

        vac_ll = base.get("vac") or base.get("vac_ll")

        fases = base.get("fases", 1)
        fp = base.get("fp", 1.0)

        if vac_ll:

            ee["vac_ll"] = vac_ll

            if fases == 3:
                ee["vac_ln"] = vac_ll / math.sqrt(3)
            else:
                ee["vac_ln"] = vac_ll

    if not vac_ll:
        raise ValueError("Voltaje AC del sistema no definido en proyecto")

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
    # Corrientes DC nominales
    # ------------------------------------------------------

    if lista:

        s0 = lista[0]

        imp = float(s0.get("imp_string_a", 0))
        isc = float(s0.get("isc_string_a", 0))

        n_strings = int(rec.get("n_strings_total", 0))

        if imp > 0 and n_strings > 0:
            ee["idc_nom"] = imp * n_strings

        if isc > 0 and n_strings > 0:
            ee["isc_total_a"] = isc * n_strings

    # ------------------------------------------------------
    # 4. Generación de circuitos MPPT
    # ------------------------------------------------------

    if lista:

        s0 = lista[0]

        imp = float(s0.get("imp_string_a", 0))
        isc = float(s0.get("isc_string_a", 0))

        n_strings = int(rec.get("n_strings_total", 0))

        mppts = int(s0.get("mppt", 2))

        circuitos_mppt = crear_circuitos_mppt(
            strings_totales=n_strings,
            mppts=mppts,
            imp=imp,
        )

        ee["dc_circuitos"] = circuitos_mppt

    # ------------------------------------------------------
    # Datos para motor de corrientes
    # ------------------------------------------------------

    if lista:

        s0 = lista[0]

        ee["strings"] = {
            "corrientes_input": {

                "imp_string_a": float(s0.get("imp_string_a", 0)),
                "isc_string_a": float(s0.get("isc_string_a", 0)),

                # se mantiene para compatibilidad con motor actual
                "strings_por_mppt": int(s0.get("n_paralelo", 1)),
                "n_strings_total": int(rec.get("n_strings_total", 0)),
            },
            "panel_i": float(s0.get("isc_string_a", 0))
        }

        ee["inversor"] = {

            "kw_ac": kw_ac,

            "v_ac_nom_v": vac_ll,
            "fases": fases,
            "fp": fp,

            "mppt": int(s0.get("mppt", 2)),
        }

    # ------------------------------------------------------
    # 5. Construcción paquete NEC
    # ------------------------------------------------------

    paquete = armar_paquete_nec(ee)

    return {
        "ok": True,
        "input": ee,
        "paq": paquete,
    }
