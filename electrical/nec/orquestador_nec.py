from typing import Dict, Any
import math

from core.dominio.contrato import ResultadoSizing
from electrical.paquete_nec import armar_paquete_nec
from electrical.circuitos.generador_circuitos_dc import generar_circuitos_dc


# ==========================================================
# Leer base eléctrica del proyecto
# ==========================================================

def _leer_base_electrica(p):

    if isinstance(p, dict):
        base = p.get("electrico", {})
    else:
        base = getattr(p, "electrico", {})

    vac_ll = base.get("vac") or base.get("vac_ll")
    fases = base.get("fases", 1)
    fp = base.get("fp", 1.0)

    return vac_ll, fases, fp


# ==========================================================
# Corrientes DC por string
# ==========================================================

def _calcular_corrientes_string(strings: Dict[str, Any]):

    imp = strings.get("i_operacion_a", 0)
    isc = strings.get("isc_a", 0)

    i_nom = imp
    i_dis = isc * 1.25

    return {
        "i_nominal": i_nom,
        "i_diseno": i_dis
    }


# ==========================================================
# Corrientes AC
# ==========================================================

def _calcular_corrientes_ac(potencia_ac_w, vac_ll, fases, fp):

    if fases == 3:
        i_nom = potencia_ac_w / (math.sqrt(3) * vac_ll * fp)
    else:
        i_nom = potencia_ac_w / (vac_ll * fp)

    i_dis = i_nom * 1.25

    return {
        "i_nominal": i_nom,
        "i_diseno": i_dis
    }


# ==========================================================
# Circuitos MPPT
# ==========================================================

def _generar_circuitos_mppt(strings: Dict[str, Any], sizing: ResultadoSizing):

    strings_totales = strings.get("strings_total", 1)
    imp = strings.get("i_operacion_a", 0)

    mppts = getattr(sizing, "mppts", 1)

    circuitos = generar_circuitos_dc(
        strings_totales,
        mppts,
        imp
    )

    return circuitos


# ==========================================================
# Resumen DC del sistema
# ==========================================================

def _armar_resumen_dc(strings: Dict[str, Any], sizing: ResultadoSizing):

    potencia_dc = sizing.pdc_kw * 1000

    vdc_nom = strings.get("vmp_string_v", 0)

    if vdc_nom > 0:
        idc_nom = potencia_dc / vdc_nom
    else:
        idc_nom = 0

    return {
        "potencia_dc_w": potencia_dc,
        "vdc_nom": vdc_nom,
        "idc_nom": idc_nom
    }

# ==========================================================
# Orquestador NEC principal
# ==========================================================

def ejecutar_nec(
    p,
    sizing: ResultadoSizing,
    strings: Dict[str, Any],
) -> Dict[str, Any]:

    ee: Dict[str, Any] = {}

    # ------------------------------------------------------
    # Base eléctrica
    # ------------------------------------------------------

    vac_ll, fases, fp = _leer_base_electrica(p)

    # ------------------------------------------------------
    # Corriente por string
    # ------------------------------------------------------

    corr_string = _calcular_corrientes_string(strings)

    # ------------------------------------------------------
    # Circuitos MPPT
    # ------------------------------------------------------

    circuitos_mppt = _generar_circuitos_mppt(strings, sizing)

    i_mppt_nom = max(c["i_operacion"] for c in circuitos_mppt)
    i_mppt_dis = max(c["i_diseno"] for c in circuitos_mppt)

    # ------------------------------------------------------
    # Corrientes AC
    # ------------------------------------------------------

    potencia_ac = sizing.kw_ac * 1000

    corr_ac = _calcular_corrientes_ac(
        potencia_ac,
        vac_ll,
        fases,
        fp
    )

    # ------------------------------------------------------
    # Resumen DC
    # ------------------------------------------------------

    dc = _armar_resumen_dc(strings, sizing)

    # ------------------------------------------------------
    # Consolidación
    # ------------------------------------------------------

    ee["corrientes"] = {

        "string": corr_string,

        "mppt": {
            "i_nominal": i_mppt_nom,
            "i_diseno": i_mppt_dis
        },

        "dc_inversor": {
            "i_nominal": dc["idc_nom"],
            "i_diseno": dc["idc_nom"] * 1.25
        },

        "ac_salida": corr_ac
    }

    ee["dc"] = dc

    ee["ac"] = {
        "potencia_ac_w": potencia_ac,
        "vac_ll": vac_ll,
        "fases": fases,
        "fp": fp,
        "iac_nom": corr_ac["i_nominal"]
    }

    ee["circuitos_mppt"] = circuitos_mppt

    # ------------------------------------------------------
    # Generar paquete NEC
    # ------------------------------------------------------

    paquete = armar_paquete_nec(ee)

    ee.update(paquete)

    return ee
