from __future__ import annotations
from typing import Any, Dict, Mapping, Optional, Tuple, Iterable

from electrical.conductores.calculo_conductores import tramo_conductor
from electrical.protecciones.protecciones import dimensionar_protecciones_fv
from electrical.conductores.corrientes import calcular_corrientes

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
# NORMALIZACION DE CORRIENTES PARA TABLA NEC
# ==========================================================

def _normalizar_corrientes(corrientes):

    def calc(v):
        try:
            if v is None:
                return {
                    "i_nominal": None,
                    "i_diseno": None
                }

            v = float(v)

            return {
                "i_nominal": v,
                "i_diseno": v * 1.25
            }

        except Exception:
            return {
                "i_nominal": None,
                "i_diseno": None
            }

    return {

        "string": calc(corrientes.get("string", {}).get("i_operacion_a")),

        "mppt": calc(corrientes.get("mppt", {}).get("i_operacion_a")),

        "dc_inversor": calc(corrientes.get("dc_total", {}).get("i_operacion_a")),

        "ac_salida": calc(corrientes.get("ac", {}).get("i_operacion_a")),
    }


# ==========================================================
# CORRIENTES NOMINALES (solo referencia)
# ==========================================================

def _resolver_corrientes_nominales(entrada: Mapping[str, Any]):

    warnings = []

    pdc_w = _num(entrada, "potencia_dc_w")
    pac_w = _num(entrada, "potencia_ac_w")

    vdc = _num(entrada, "vdc_nom")
    vac_ll = _num(entrada, "vac_ll")
    vac_ln = _num(entrada, "vac_ln")

    fases = _entero(entrada, "fases")
    fp = _num(entrada, "fp") or 1.0

    idc = None
    if pdc_w and vdc:
        idc = pdc_w / vdc

    iac = None
    if pac_w:
        if fases == 3 and vac_ll:
            iac = pac_w / (_sqrt3() * vac_ll * fp)
        elif vac_ln or vac_ll:
            v = vac_ln or vac_ll
            iac = pac_w / (v * fp)

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
# CORRIENTES FV
# ==========================================================

def _resolver_corrientes_fv(entrada: Mapping[str, Any]):

    strings_result = entrada.get("strings") or {}
    inversor_data = entrada.get("inversor") or {}

    strings_data = strings_result.get("corrientes_input")

    n_strings = entrada.get("n_strings")

    if not strings_data:
        raise ValueError("No llegaron datos corrientes_input desde strings")

    if not n_strings:
        raise ValueError("n_strings_total inválido para cálculo de corrientes")

    return calcular_corrientes(
        strings=strings_data,
        inv=inversor_data,
        cfg_tecnicos={
            "n_strings_total": n_strings
        }
    )

# ==========================================================
# PROTECCIONES
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
# CONDUCTORES
# ==========================================================

def _resolver_conductores(entrada, dc, ac, corrientes):

    warnings = []
    circuitos = []

    try:

        i_dc_diseno = corrientes.get("dc_total", {}).get("i_diseno_nec_a")

        if i_dc_diseno:

            circuitos.append(
                tramo_conductor(
                    nombre="DC",
                    i_diseno_a=i_dc_diseno,
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
# CANALIZACION
# ==========================================================

def _resolver_canalizacion(entrada, dc, ac, ocpd, conductores):

    if not callable(canalizacion_fv):
        return None, ["Canalización no disponible"]

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
# RESUMEN PDF
# ==========================================================

def _armar_resumen(dc, ac, ocpd, conductores, warnings):

    circuitos = conductores.get("circuitos") or []

    dc_tramo = next((c for c in circuitos if c.get("nombre") == "DC"), None)
    ac_tramo = next((c for c in circuitos if c.get("nombre") == "AC"), None)

    idc = dc.get("idc_nom")
    iac = ac.get("iac_nom")

    return {
        "idc_nom": float(idc) if idc else None,
        "iac_nom": float(iac) if iac else None,
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
# ORQUESTADOR NEC
# ==========================================================

def armar_paquete_nec(entrada: Mapping[str, Any]) -> Dict[str, Any]:

    warnings = []

    dc, ac, w = _resolver_corrientes_nominales(entrada)
    warnings = _merge(warnings, w)

    try:
        corrientes = _resolver_corrientes_fv(entrada)
    except Exception as e:

        corrientes = {
            "panel": {"i_operacion_a": None},
            "string": {"i_operacion_a": None},
            "mppt": {"i_operacion_a": None},
            "dc_total": {"i_operacion_a": None},
            "ac": {"i_operacion_a": None},
        }

        warnings.append(f"Corrientes error: {e}")

    corrientes_nec = _normalizar_corrientes(corrientes)

    ocpd, w = _resolver_protecciones(entrada, ac)
    warnings = _merge(warnings, w)

    conductores, w = _resolver_conductores(
        entrada,
        dc,
        ac,
        corrientes
    )

    warnings = _merge(warnings, w)

    canalizacion, w = _resolver_canalizacion(
        entrada,
        dc,
        ac,
        ocpd,
        conductores
    )

    warnings = _merge(warnings, w)

    if corrientes and "ac" in corrientes:
        ac["iac_nom"] = corrientes["ac"].get("i_operacion_a")

    resumen = _armar_resumen(dc, ac, ocpd, conductores, warnings)

    return {

        "corrientes": corrientes_nec,
        "corrientes_raw": corrientes,

        "dc": dc,
        "ac": ac,

        "ocpd": ocpd,
        "conductores": conductores,

        "canalizacion": canalizacion,

        "warnings": warnings,
        "resumen_pdf": resumen,
    }
