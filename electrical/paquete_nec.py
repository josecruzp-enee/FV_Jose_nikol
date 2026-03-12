from __future__ import annotations

"""
ORQUESTADOR DE INGENIERÍA ELÉCTRICA FV

Este módulo coordina todos los cálculos eléctricos del sistema FV.

FRONTERA DEL DOMINIO
--------------------

Entrada:
    datos eléctricos del sistema

Salida:
    paquete completo de ingeniería eléctrica

Este módulo NO realiza cálculos físicos complejos.
Solo coordina los módulos eléctricos:

    corrientes
    protecciones
    conductores
    canalizacion
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

    iac = corrientes.get("ac", {}).get("i_operacion_a")

    return dimensionar_protecciones_fv(
        iac_nom_a=iac,
        n_strings=entrada["n_strings"],
        isc_mod_a=entrada.get("isc_mod_a", 0)
    )


# ==========================================================
# CONDUCTORES
# ==========================================================

def _resolver_conductores(entrada, corrientes):

    circuitos = []

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

    return {"circuitos": circuitos}


# ==========================================================
# CANALIZACIÓN
# ==========================================================

def _resolver_canalizacion(entrada, corrientes, protecciones, conductores):

    if not callable(canalizacion_fv):
        return None

    return canalizacion_fv(
        entrada=entrada,
        corrientes=corrientes,
        ocpd=protecciones,
        conductores=conductores,
    )


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
    # Resultado consolidado
    # ------------------------------------------------------

    return {

        "ok": True,

        "corrientes": corrientes,

        "protecciones": protecciones,

        "conductores": conductores,

        "canalizacion": canalizacion,
    }


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# ejecutar_ingenieria_electrica()
#
# Entrada:
#   datos eléctricos del sistema FV
#
# Salida:
#   paquete completo de ingeniería eléctrica
#
# Consumido por:
#   core.orquestador_estudio
#
# ==========================================================
