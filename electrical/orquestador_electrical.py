from __future__ import annotations

from electrical.paneles.resultado_paneles import ResultadoPaneles

from electrical.conductores.corrientes import (
    calcular_corrientes,
    CorrientesInput,
)

from electrical.conductores.calculo_conductores import (
    dimensionar_tramos_fv as calcular_conductores,
)

from electrical.conductores.resultado_conductores import ResultadoConductores

from electrical.protecciones.protecciones import (
    calcular_protecciones,
    EntradaProtecciones,
)

from electrical.resultado_electrical import ResultadoElectrico

# 🔥 VALIDADOR
from electrical.validacion_fv import validar_sistema_fv


# ==========================================================
# ORQUESTADOR ELECTRICAL
# ==========================================================

def ejecutar_electrical(*args, **kwargs) -> ResultadoElectrico:

    if args:
        if len(args) == 2:
            datos, paneles = args
            kwargs["datos"] = datos
            kwargs["paneles"] = paneles

    paneles = kwargs.get("paneles")
    datos = kwargs.get("datos")
    sizing = kwargs.get("sizing")

    try:

        print("\n⚡ [ELECTRICAL] INICIO")

        # ==================================================
        # VALIDACIONES BASE
        # ==================================================
        if not paneles or not paneles.ok:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=_corrientes_error("Paneles inválidos"),
                conductores=_conductores_error("Paneles inválidos"),
                protecciones=_protecciones_error("Paneles inválidos"),
            )

        if not sizing:
            raise ValueError("Falta sizing en electrical")

        # ==================================================
        # 🔥 USAR RESULTADO DE PANELES (NO RECALCULAR)
        # ==================================================
        panel_obj = getattr(paneles, "panel", None) or getattr(paneles, "panel_spec", None)

        if panel_obj is None:
            raise ValueError("No se pudo obtener panel desde ResultadoPaneles")

        strings = paneles.strings
        array = paneles.array

        if not strings or not array:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=_corrientes_error("Strings no disponibles desde paneles"),
                conductores=_conductores_error("Strings no disponibles desde paneles"),
                protecciones=_protecciones_error("Strings no disponibles desde paneles"),
            )

        print("DEBUG STRINGS (desde paneles):", strings)
        print("DEBUG ARRAY (desde paneles):", array)

        # ==================================================
        # 🔥 VALIDACIÓN GLOBAL FV
        # ==================================================
        val = validar_sistema_fv(
            panel=panel_obj,
            inversor=sizing.inversor,
            array=array,
            strings=strings
        )

        if not val["ok"]:
            print("❌ VALIDACIÓN FV FALLIDA:")
            for err in val["errores"]:
                print(" -", err)

            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=_corrientes_error("Validación FV fallida"),
                conductores=_conductores_error("Validación FV fallida"),
                protecciones=_protecciones_error("Validación FV fallida"),
            )

        if val["warnings"]:
            print("⚠ WARNINGS FV:")
            for w in val["warnings"]:
                print(" -", w)

        # ==================================================
        # PARAMETROS ELECTRICOS
        # ==================================================
        inst = getattr(datos, "instalacion_electrica", None)

        if inst is None:
            raise ValueError("No existe instalacion_electrica en datos")

        if isinstance(inst, dict):
            vac = inst.get("vac")
            fases = inst.get("fases", 1)
            fp = inst.get("fp", 1.0)
            dist_dc_m = inst.get("dist_dc_m")
            dist_ac_m = inst.get("dist_ac_m")
        else:
            vac = getattr(inst, "vac", None)
            fases = getattr(inst, "fases", 1)
            fp = getattr(inst, "fp", 1.0)
            dist_dc_m = getattr(inst, "dist_dc_m", None)
            dist_ac_m = getattr(inst, "dist_ac_m", None)

        if vac is None:
            raise ValueError("Falta 'vac' en instalacion_electrica")

        if dist_dc_m is None or dist_ac_m is None:
            raise ValueError("Faltan distancias en instalacion_electrica")

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
        tramos = calcular_conductores(
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


# ==================================================
# HELPERS DE ERROR
# ==================================================

def _corrientes_error(msg: str):
    from electrical.conductores.resultado_corriente import ResultadoCorrientes
    return ResultadoCorrientes.error(msg)


def _conductores_error(msg: str):
    from electrical.conductores.resultado_conductores import ResultadoConductores
    return ResultadoConductores.error(msg)


def _protecciones_error(msg: str):
    from electrical.protecciones.resultado_protecciones import ResultadoProtecciones
    return ResultadoProtecciones.error(msg)
