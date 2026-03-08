from __future__ import annotations
from typing import Any, Dict, Mapping, Optional, Tuple, Iterable

from electrical.conductores.calculo_conductores import tramo_conductor
from electrical.protecciones.protecciones import dimensionar_protecciones_fv
from electrical.conductores.corrientes import calcular_corrientes


# Opcionales
try:
    from electrical.protecciones.spd import recomendar_spd
except Exception:
    recomendar_spd = None

try:
    from electrical.protecciones.seccionamiento import recomendar_seccionamiento
except Exception:
    recomendar_seccionamiento = None

try:
    from electrical.canalizacion.canalizacion import canalizacion_fv
except Exception:
    canalizacion_fv = None


# ==========================================================
# UTILIDADES
# ==========================================================

def _num(m: Mapping[str, Any], *keys: str) -> Optional[float]:
    for k in keys:
        if k in m and m[k] is not None:
            try:
                return float(m[k])
            except Exception:
                return None
    return None


def _entero(m: Mapping[str, Any], *keys: str) -> Optional[int]:
    for k in keys:
        if k in m and m[k] is not None:
            try:
                return int(m[k])
            except Exception:
                return None
    return None


def _merge(base: Iterable[str], *more: Iterable[str]) -> list[str]:
    out = list(base or [])
    for group in more:
        for w in group or []:
            if w and w not in out:
                out.append(str(w))
    return out


def _sqrt3() -> float:
    return 1.7320508075688772


# ==========================================================
# 1️⃣ CORRIENTES NOMINALES (DC / AC)
# ==========================================================

def _resolver_corrientes_nominales(entrada: Mapping[str, Any]) -> Tuple[Dict, Dict, list[str]]:

    warnings = []

    pdc_w = _num(entrada, "potencia_dc_w")
    if pdc_w is None:
        pdc_kw = _num(entrada, "potencia_dc_kw")
        if pdc_kw is not None:
            pdc_w = pdc_kw * 1000

    pac_w = _num(entrada, "potencia_ac_w")
    if pac_w is None:
        pac_kw = _num(entrada, "potencia_ac_kw")
        if pac_kw is not None:
            pac_w = pac_kw * 1000

    vdc = _num(entrada, "vdc_nom")
    vac_ll = _num(entrada, "vac_ll")
    vac_ln = _num(entrada, "vac_ln")

    fases = _entero(entrada, "fases")
    fp = _num(entrada, "fp") or 1.0

    idc = None
    if pdc_w and vdc and vdc > 0:
        idc = pdc_w / vdc
    else:
        warnings.append("No se pudo calcular idc_nom.")

    iac = None
    if pac_w:
        if fases == 3 and vac_ll:
            iac = pac_w / (_sqrt3() * vac_ll * fp)
        elif vac_ln or vac_ll:
            v = vac_ln or vac_ll
            iac = pac_w / (v * fp)

    if iac is None:
        warnings.append("No se pudo calcular iac_nom.")

    dc = {
        "potencia_dc_w": pdc_w,
        "vdc_nom": vdc,
        "idc_nom": idc,
    }

    ac = {
        "potencia_ac_w": pac_w,
        "vac_ll": vac_ll,
        "vac_ln": vac_ln,
        "fases": fases,
        "fp": fp,
        "iac_nom": iac,
    }

    return dc, ac, warnings


# ==========================================================
# 2️⃣ PROTECCIONES
# ==========================================================

def _resolver_protecciones(entrada, ac):

    warnings = []

    try:

        iac = float(ac.get("iac_nom") or 0.0)

        n_strings = int(entrada.get("n_strings", 1))
        isc_mod = float(entrada.get("isc_mod_a", 0.0))

        ocpd = dimensionar_protecciones_fv(
            iac_nom_a=iac,
            n_strings=n_strings,
            isc_mod_a=isc_mod,
        )

    except Exception as e:

        warnings.append(f"OCPD error: {e}")
        ocpd = None

    return ocpd, warnings


# ==========================================================
# 3️⃣ CONDUCTORES
# ==========================================================

def _resolver_conductores(entrada, dc, ac):

    warnings = []
    circuitos = []

    try:

        if dc.get("idc_nom"):

            circuitos.append(
                tramo_conductor(
                    nombre="DC",
                    i_diseno_a=dc["idc_nom"],
                    v_base_v=dc.get("vdc_nom") or 1,
                    l_m=entrada.get("dist_dc_m", 1),
                    vd_obj_pct=entrada.get("vdrop_obj_dc_pct", 2),
                )
            )

        if ac.get("iac_nom"):

            circuitos.append(
                tramo_conductor(
                    nombre="AC",
                    i_diseno_a=ac["iac_nom"],
                    v_base_v=ac.get("vac_ll") or ac.get("vac_ln") or 1,
                    l_m=entrada.get("dist_ac_m", 1),
                    vd_obj_pct=entrada.get("vdrop_obj_ac_pct", 2),
                )
            )

    except Exception as e:

        warnings.append(f"Conductores error: {e}")

    return {"circuitos": circuitos}, warnings


# ==========================================================
# 4️⃣ CANALIZACIÓN
# ==========================================================

def _resolver_canalizacion(entrada, dc, ac, ocpd, conductores):

    if not callable(canalizacion_fv):
        return None, ["Canalización no disponible."]

    try:

        return canalizacion_fv(
            entrada=entrada,
            dc=dc,
            ac=ac,
            ocpd=ocpd,
            conductores=conductores,
        ), []

    except Exception as e:

        return None, [f"Canalización error: {e}"]


# ==========================================================
# 5️⃣ RESUMEN PDF
# ==========================================================

def _armar_resumen(dc, ac, ocpd, conductores, warnings):

    circuitos = conductores.get("circuitos") or []

    dc_tramo = next((c for c in circuitos if c.get("nombre") == "DC"), None)
    ac_tramo = next((c for c in circuitos if c.get("nombre") == "AC"), None)

    return {
        "idc_nom": dc.get("idc_nom"),
        "iac_nom": ac.get("iac_nom"),
        "breaker_ac": (
            ocpd.get("breaker_ac", {}).get("tamano_a")
            if isinstance(ocpd, dict)
            else None
        ),
        "conductor_dc": dc_tramo.get("calibre") if dc_tramo else None,
        "conductor_ac": ac_tramo.get("calibre") if ac_tramo else None,
        "warnings": warnings,
    }


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================

def armar_paquete_nec(entrada: Mapping[str, Any]) -> Dict[str, Any]:

    if not isinstance(entrada, Mapping):
        raise TypeError("entrada debe ser Mapping.")

    warnings = []

    # ======================================================
    # Corrientes nominales (DC / AC del sistema)
    # ======================================================

    dc, ac, w = _resolver_corrientes_nominales(entrada)
    warnings = _merge(warnings, w)

    # ======================================================
    # ADAPTAR STRINGS → MOTOR CORRIENTES
    # ======================================================

    try:

        strings_result = entrada.get("strings", {})

        strings_list = strings_result.get("strings", [])

        if strings_list:

            s0 = strings_list[0]

            strings_data = {
                "imp_string_a": float(s0.get("imp_a", 0)),
                "isc_string_a": float(s0.get("isc_a", 0)),
                "strings_por_mppt": int(s0.get("n_paralelo", 1)),
                "n_strings_total": int(
                    strings_result.get("recomendacion", {}).get(
                        "n_strings_total", 0
                    )
                ),
            }

        else:

            strings_data = strings_result.get("corrientes_input", {})

        inversor_data = entrada.get("inversor", {})

        corrientes = calcular_corrientes(
            strings=strings_data,
            inv=inversor_data,
            cfg_tecnicos={}
        )

    except Exception as e:

        corrientes = {
            "panel": {"i_operacion_a": 0},
            "string": {"i_operacion_a": 0},
            "mppt": {"i_operacion_a": 0},
            "dc_total": {"i_operacion_a": 0},
            "ac": {"i_operacion_a": 0},
        }

        warnings.append(f"Corrientes error: {e}")

    # ======================================================
    # PROTECCIONES
    # ======================================================

    ocpd, w = _resolver_protecciones(entrada, ac)
    warnings = _merge(warnings, w)

    # ======================================================
    # CONDUCTORES
    # ======================================================

    conductores, w = _resolver_conductores(entrada, dc, ac)
    warnings = _merge(warnings, w)

    # ======================================================
    # CANALIZACIÓN
    # ======================================================

    canalizacion, w = _resolver_canalizacion(
        entrada,
        dc,
        ac,
        ocpd,
        conductores
    )

    warnings = _merge(warnings, w)

    # ======================================================
    # RESUMEN PDF
    # ======================================================

    resumen = _armar_resumen(dc, ac, ocpd, conductores, warnings)

    # ======================================================
    # RESULTADO FINAL
    # ======================================================

    return {

        "corrientes": corrientes,

        "dc": dc,
        "ac": ac,

        "ocpd": ocpd,

        "conductores": conductores,

        "canalizacion": canalizacion,

        "warnings": warnings,

        "resumen_pdf": resumen,
    }
