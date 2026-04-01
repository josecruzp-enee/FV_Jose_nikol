from __future__ import annotations
from typing import Any

# ===============================
# DOMINIO
# ===============================
from electrical.resultado_electrical import ResultadoElectrico
from electrical.conductores.calculo_conductores import dimensionar_tramos_fv
# ===============================
# SUBMÓDULOS
# ===============================
from electrical.validacion_fv import validar_sistema_fv

from electrical.conductores.corrientes import (
    CorrientesInput,
    calcular_corrientes,
)



from electrical.protecciones.protecciones import (
    EntradaProtecciones,
    calcular_protecciones,
)

from electrical.conductores.resultado_conductores import ResultadoConductores
from electrical.conductores.resultado_corriente import ResultadoCorrientes
from electrical.protecciones.resultado_protecciones import ResultadoProtecciones

# ==========================================================
# HELPERS DE ERROR (NO ROMPEN FLUJO)
# ==========================================================
def _corrientes_error(msg: str):
    return ResultadoCorrientes.error(msg)


def _conductores_error(msg: str):
    return ResultadoConductores.error(msg)


def _protecciones_error(msg: str):
    return ResultadoProtecciones.error(msg)


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================
def ejecutar_electrical(*, datos: Any, paneles: Any, sizing: Any) -> ResultadoElectrico:

    try:
        print("\n⚡ [ELECTRICAL] INICIO")

        # ==================================================
        # VALIDACIONES BASE
        # ==================================================
        if not paneles or not getattr(paneles, "ok", False):
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=_corrientes_error("Paneles inválidos"),
                conductores=_conductores_error("Paneles inválidos"),
                protecciones=_protecciones_error("Paneles inválidos"),
            )

        if not sizing:
            raise ValueError("Falta sizing en electrical")

        if not getattr(sizing, "kw_ac", None):
            raise ValueError("kw_ac inválido o en cero desde sizing")

        # ==================================================
        # DATOS DESDE PANELES
        # ==================================================
        panel_obj = getattr(paneles, "panel", None)

        strings = getattr(paneles, "strings", None)
        array = getattr(paneles, "array", None)

        if not strings or not array:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=_corrientes_error("Strings no disponibles"),
                conductores=_conductores_error("Strings no disponibles"),
                protecciones=_protecciones_error("Strings no disponibles"),
            )

        print("DEBUG STRINGS:", strings)
        print("DEBUG ARRAY:", array)

        # ==================================================
        # INVERSOR
        # ==================================================
        inversor = getattr(sizing, "inversor", None)
        if inversor is None:
            raise ValueError("Sizing no contiene inversor")

        # ==================================================
        # VALIDACIÓN FV
        # ==================================================
        val = validar_sistema_fv(
            panel=panel_obj,
            inversor=inversor,
            array=array,
            strings=strings,
        )

        if not val["ok"]:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=_corrientes_error("Validación FV fallida"),
                conductores=_conductores_error("Validación FV fallida"),
                protecciones=_protecciones_error("Validación FV fallida"),
            )

        # ==================================================
        # PARÁMETROS ELÉCTRICOS
        # ==================================================
        inst = getattr(datos, "electrico", None)

        if inst is None:
            raise ValueError("datos.electrico es obligatorio")

        if not isinstance(inst, dict):
            raise ValueError("electrico debe ser dict")

        vac = inst.get("vac")
        fases = inst.get("fases")
        fp = inst.get("fp")
        dist_dc_m = inst.get("dist_dc_m")
        dist_ac_m = inst.get("dist_ac_m")

        # ==============================
        # VALIDACIÓN RÍGIDA
        # ==============================

        if vac is None:
            raise ValueError("vac no definido en electrico")

        if fases is None:
            raise ValueError("fases no definido en electrico")

        if fp is None:
            raise ValueError("fp no definido en electrico")

        if dist_dc_m is None:
            raise ValueError("dist_dc_m no definido en electrico")

        if dist_ac_m is None:
            raise ValueError("dist_ac_m no definido en electrico")



        
        # ==================================================
        # CORRIENTES
        # ==================================================
        corrientes_input = CorrientesInput(
            paneles=paneles,
            kw_ac=sizing.kw_ac,
            vac=vac,
            fases=fases,
            fp=fp,
        )

        corrientes = calcular_corrientes(corrientes_input)

        print("DEBUG CORRIENTES:", corrientes)

        if not corrientes.ok:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=corrientes,
                conductores=_conductores_error("Corrientes inválidas"),
                protecciones=_protecciones_error("Corrientes inválidas"),
            )

        # ==================================================
        # CONDUCTORES
        # ==================================================
        tramos = dimensionar_tramos_fv(
            corrientes=corrientes,
            vmp_dc=array.vdc_nom,
            vac=vac,
            dist_dc_m=dist_dc_m,
            dist_ac_m=dist_ac_m,
            fases=fases,
        )

        conductores = ResultadoConductores.build(tramos)


        
        if not conductores.ok:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=corrientes,
                conductores=conductores,
                protecciones=_protecciones_error("Conductores inválidos"),
            )

        # ==================================================
        # PROTECCIONES
        # ==================================================
        entrada_prot = EntradaProtecciones(
            corrientes=corrientes,
            n_strings=array.n_strings_total,
            paneles=paneles,
        )

        protecciones = calcular_protecciones(entrada_prot)

        print("DEBUG PROTECCIONES:", protecciones)

        # ==================================================
        # RESULTADO FINAL
        # ==================================================
        print("⚡ [ELECTRICAL] OK")

        return ResultadoElectrico.build(
            paneles=paneles,
            corrientes=corrientes,
            conductores=conductores,
            protecciones=protecciones,
        )

    except Exception as e:
        print("🔥 ERROR ELECTRICAL:", str(e))

        return ResultadoElectrico.build(
            paneles=paneles,
            corrientes=_corrientes_error(str(e)),
            conductores=_conductores_error(str(e)),
            protecciones=_protecciones_error(str(e)),
        )
