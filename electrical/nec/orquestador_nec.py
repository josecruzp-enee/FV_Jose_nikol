from typing import Dict, Any
import math

from core.dominio.contrato import ResultadoSizing
from electrical.paquete_nec import armar_paquete_nec
from electrical.circuitos.generador_circuitos_dc import generar_circuitos_dc


# ==========================================================
# UTILIDAD: obtener lista de strings
# ==========================================================

def _lista_strings(strings):

    if not strings:
        return []

    if isinstance(strings, dict):
        return strings.get("strings", [])

    if hasattr(strings, "strings"):
        return strings.strings

    if isinstance(strings, list):
        return strings

    return []


# ==========================================================
# Leer base eléctrica
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

def _calcular_corrientes_string(strings):

    lista = _lista_strings(strings)

    if not lista:
        return {"i_nominal": 0, "i_diseno": 0, "isc": 0}

    s0 = lista[0]

    if isinstance(s0, dict):
        imp = s0.get("imp_a", 0)
        isc = s0.get("isc_a", 0)
    else:
        imp = getattr(s0, "imp_a", 0)
        isc = getattr(s0, "isc_a", 0)

    i_nom = imp
    i_dis = isc * 1.25

    return {
        "i_nominal": i_nom,
        "i_diseno": i_dis,
        "isc": isc
    }


# ==========================================================
# Circuitos MPPT
# ==========================================================

def _generar_circuitos_mppt(strings, sizing: ResultadoSizing):

    lista = _lista_strings(strings)

    strings_totales = len(lista)

    if lista:

        s0 = lista[0]

        if isinstance(s0, dict):
            imp = s0.get("imp_a", 0)
        else:
            imp = getattr(s0, "imp_a", 0)

    else:
        imp = 0

    mppts = getattr(sizing, "mppts", 1)

    circuitos = generar_circuitos_dc(
        strings_totales,
        mppts,
        imp
    )

    return circuitos


# ==========================================================
# Corrientes AC
# ==========================================================

def _calcular_corrientes_ac(potencia_ac_w, vac_ll, fases, fp):

    if not vac_ll:
        return {"i_nominal": 0, "i_diseno": 0}

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
# Resumen DC
# ==========================================================

def _armar_resumen_dc(strings, sizing: ResultadoSizing):

    lista = _lista_strings(strings)

    potencia_dc = getattr(sizing, "pdc_kw", 0) * 1000

    if lista:

        s0 = lista[0]

        if isinstance(s0, dict):
            vdc_nom = s0.get("vmp_string_v", 0)
        else:
            vdc_nom = getattr(s0, "vmp_string_v", 0)

    else:
        vdc_nom = 0

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
# ORQUESTADOR NEC
# ==========================================================

def ejecutar_nec(
    p,
    sizing: ResultadoSizing,
    strings,
) -> Dict[str, Any]:

    ee: Dict[str, Any] = {}

    # ------------------------------------------------------
    # FRONTERA 1: STRINGS → NEC
    # ------------------------------------------------------

    print("\n==============================")
    print("FRONTERA 1: STRINGS → NEC")
    print("==============================")
    print("strings recibidos:", strings)

    # ------------------------------------------------------
    # Base eléctrica
    # ------------------------------------------------------

    vac_ll, fases, fp = _leer_base_electrica(p)

    # ------------------------------------------------------
    # Corrientes string
    # ------------------------------------------------------

    corr_string = _calcular_corrientes_string(strings)

    print("\nCorrientes calculadas del string:", corr_string)

    # ------------------------------------------------------
    # Circuitos MPPT
    # ------------------------------------------------------

    circuitos_mppt = _generar_circuitos_mppt(strings, sizing)

    print("\nCircuitos MPPT generados:", circuitos_mppt)

    i_mppt_nom = max((c.get("i_operacion", 0) for c in circuitos_mppt), default=0)
    i_mppt_dis = max((c.get("i_diseno", 0) for c in circuitos_mppt), default=0)

    # ------------------------------------------------------
    # Corrientes AC
    # ------------------------------------------------------

    potencia_ac = getattr(sizing, "kw_ac", 0) * 1000

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
    # Consolidación interna
    # ------------------------------------------------------

    ee["corrientes"] = {

        "string": {
            "i_nominal": corr_string["i_nominal"],
            "i_diseno": corr_string["i_diseno"]
        },

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
    # ENTRADA PARA PAQUETE NEC
    # ------------------------------------------------------

    lista = _lista_strings(strings)

    entrada_nec = {

        "n_strings": len(lista),

        "imp_string_a": corr_string["i_nominal"],
        "isc_string_a": corr_string["isc"],

        "potencia_dc_w": dc["potencia_dc_w"],
        "potencia_ac_w": potencia_ac,

        "vdc_nom": dc["vdc_nom"],
        "vac_ll": vac_ll,

        "fases": fases,
        "fp": fp,
    }

    # ------------------------------------------------------
    # FRONTERA 2: NEC → PAQUETE NEC
    # ------------------------------------------------------

    print("\n==============================")
    print("FRONTERA 2: NEC → PAQUETE NEC")
    print("==============================")
    print("entrada_nec:", entrada_nec)

    # ------------------------------------------------------
    # Ejecutar NEC
    # ------------------------------------------------------

    paquete = armar_paquete_nec(entrada_nec)

    print("\n==============================")
    print("FRONTERA 3: SALIDA PAQUETE NEC")
    print("==============================")
    print(paquete)

    ee.update(paquete)

    return ee
