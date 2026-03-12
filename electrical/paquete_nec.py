from __future__ import annotations

"""
ORQUESTADOR DE INGENIERÍA ELÉCTRICA — FV ENGINE

FRONTERA DEL DOMINIO
--------------------
Este módulo es la frontera del dominio eléctrico del sistema FV.

core
   ↓
ingenieria_electrica  ← ESTE MÓDULO
   ↓
corrientes
protecciones
conductores
canalizacion

Responsabilidad
---------------
Coordinar los cálculos eléctricos del sistema FV y devolver un
paquete eléctrico consolidado.

Este módulo NO implementa modelos físicos complejos.
Solo coordina módulos eléctricos especializados.


ENTRADA
-------
entrada : Mapping[str, Any]

Estructura esperada:

entrada = {

    "strings": {
        "corrientes_input": dict
    },

    "inversor": {
        "kw_ac": float,
        "v_ac_nom_v": float,
        "fases": int,
        "fp": float
    },

    "n_strings": int,

    "isc_mod_a": float | None,

    "vdc_nom": float | None,

    "vac_ll": float | None,

    "dist_dc_m": float | None,
    "dist_ac_m": float | None,

    "vdrop_obj_dc_pct": float | None,
    "vdrop_obj_ac_pct": float | None
}


SALIDA
------
Dict[str, Any]

resultado = {

    "ok": bool,

    "corrientes": {...},

    "protecciones": {...},

    "conductores": {...},

    "canalizacion": {...},

    "warnings": list[str],

    "resumen_pdf": {

        "i_dc_nom": float | None,

        "i_ac_nom": float | None,

        "breaker_ac": int | None,

        "conductor_dc": str | None,

        "conductor_ac": str | None
    }
}
"""

from typing import Mapping, Dict, Any

from electrical.conductores.corrientes import calcular_corrientes
from electrical.protecciones.protecciones import dimensionar_protecciones_fv
from electrical.conductores.calculo_conductores import tramo_conductor

try:
    from electrical.canalizacion.canalizacion import canalizacion_fv
except Exception:
    canalizacion_fv = None


# ==========================================================
# VALIDACIÓN DE ENTRADAS
# ==========================================================

def _validar_entrada(entrada: Mapping[str, Any]):

    errores = []

    if "strings" not in entrada:
        errores.append("Faltan datos de strings.")

    if "inversor" not in entrada:
        errores.append("Faltan datos del inversor.")

    if "n_strings" not in entrada:
        errores.append("n_strings no definido.")

    return errores


# ==========================================================
# CORRIENTES
# ==========================================================

def _resolver_corrientes(entrada):

    strings = entrada["strings"]
    inversor = entrada["inversor"]

    return calcular_corrientes(
        strings=strings.get("corrientes_input"),
        inv=inversor,
        cfg_tecnicos={
            "n_strings_total": entrada["n_strings"]
        }
    )


# ==========================================================
# PROTECCIONES
# ==========================================================

def _resolver_protecciones(entrada, corrientes):

    try:

        iac = corrientes.get("ac", {}).get("i_operacion_a")

        return dimensionar_protecciones_fv(
            iac_nom_a=iac,
            n_strings=entrada["n_strings"],
            isc_mod_a=entrada.get("isc_mod_a", 0)
        )

    except Exception:

        return None


# ==========================================================
# CONDUCTORES
# ==========================================================

def _resolver_conductores(entrada, corrientes):

    circuitos = []

    try:

        dc_i = corrientes.get("dc_total", {}).get("i_diseno_nec_a")

        if dc_i:

            circuitos.append(
                tramo_conductor(
                    nombre="DC",
                    i_diseno_a=dc_i,
                    v_base_v=entrada.get("vdc_nom", 1),
                    l_m=entrada.get("dist_dc_m", 1),
                    vd_obj_pct=entrada.get("vdrop_obj_dc_pct", 2),
                )
            )

        ac_i = corrientes.get("ac", {}).get("i_operacion_a")

        if ac_i:

            circuitos.append(
                tramo_conductor(
                    nombre="AC",
                    i_diseno_a=ac_i,
                    v_base_v=entrada.get("vac_ll", 1),
                    l_m=entrada.get("dist_ac_m", 1),
                    vd_obj_pct=entrada.get("vdrop_obj_ac_pct", 2),
                )
            )

    except Exception:
        pass

    return {"circuitos": circuitos}


# ==========================================================
# CANALIZACIÓN
# ==========================================================

def _resolver_canalizacion(entrada, corrientes, protecciones, conductores):

    if not callable(canalizacion_fv):
        return None

    try:

        return canalizacion_fv(
            entrada=entrada,
            corrientes=corrientes,
            ocpd=protecciones,
            conductores=conductores,
        )

    except Exception:

        return None


# ==========================================================
# RESUMEN ELÉCTRICO
# ==========================================================

def _armar_resumen(corrientes, protecciones, conductores):

    circuitos = conductores.get("circuitos", [])

    dc = next((c for c in circuitos if c.get("nombre") == "DC"), None)
    ac = next((c for c in circuitos if c.get("nombre") == "AC"), None)

    return {

        "i_dc_nom": corrientes.get("dc_total", {}).get("i_operacion_a"),

        "i_ac_nom": corrientes.get("ac", {}).get("i_operacion_a"),

        "breaker_ac": (
            protecciones.get("breaker_ac", {}).get("tamano_a")
            if protecciones else None
        ),

        "conductor_dc": dc.get("calibre") if dc else None,

        "conductor_ac": ac.get("calibre") if ac else None,
    }


# ==========================================================
# ORQUESTADOR ELÉCTRICO
# ==========================================================

def ejecutar_ingenieria_electrica(
    entrada: Mapping[str, Any]
) -> Dict[str, Any]:

    errores = _validar_entrada(entrada)

    if errores:

        return {
            "ok": False,
            "errores": errores
        }

    warnings = []

    # ------------------------------------------------------
    # Corrientes
    # ------------------------------------------------------

    corrientes = _resolver_corrientes(entrada)

    # ------------------------------------------------------
    # Protecciones
    # ------------------------------------------------------

    protecciones = _resolver_protecciones(
        entrada,
        corrientes
    )

    # ------------------------------------------------------
    # Conductores
    # ------------------------------------------------------

    conductores = _resolver_conductores(
        entrada,
        corrientes
    )

    # ------------------------------------------------------
    # Canalización
    # ------------------------------------------------------

    canalizacion = _resolver_canalizacion(
        entrada,
        corrientes,
        protecciones,
        conductores
    )

    # ------------------------------------------------------
    # Resumen para PDF / UI
    # ------------------------------------------------------

    resumen = _armar_resumen(
        corrientes,
        protecciones,
        conductores
    )

    # ------------------------------------------------------
    # Paquete eléctrico consolidado
    # ------------------------------------------------------

    return {

        "ok": True,

        "corrientes": corrientes,

        "protecciones": protecciones,

        "conductores": conductores,

        "canalizacion": canalizacion,

        "warnings": warnings,

        "resumen_pdf": resumen,
    }
