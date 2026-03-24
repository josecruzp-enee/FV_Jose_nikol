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


# ==========================================================
# ORQUESTADOR ELECTRICAL
# ==========================================================

def ejecutar_electrical(*args, **kwargs) -> ResultadoElectrico:

    # ======================================================
    # NORMALIZADOR DE ENTRADA
    # ======================================================
    if args:
        if len(args) == 2:
            datos, paneles = args
            kwargs["datos"] = datos
            kwargs["paneles"] = paneles

    paneles = kwargs.get("paneles")
    datos = kwargs.get("datos")                 # 🔥 FIX
    sizing = kwargs.get("sizing")               # 🔥 NUEVO

    try:

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

        if not paneles.strings:
            raise ValueError("No hay strings definidos")

        # ==================================================
        # PARAMETROS ELECTRICOS
        # ==================================================
        inst = getattr(datos, "instalacion_electrica", None) or {}

        vac = inst.get("vac")
        fases = inst.get("fases", 1)
        fp = inst.get("fp", 1.0)
        dist_dc_m = inst.get("dist_dc_m")
        dist_ac_m = inst.get("dist_ac_m")

        if vac is None:
            raise ValueError("Falta 'vac' en instalacion_electrica")

        if dist_dc_m is None or dist_ac_m is None:
            raise ValueError("Faltan distancias en instalacion_electrica")

        # ==================================================
        # CORRIENTES (FIX REAL)
        # ==================================================
        corrientes_input = CorrientesInput(
            paneles=paneles,
            kw_ac=sizing.kw_ac,   # 🔥 FIX CRITICO
            vac=vac,
            fases=fases,
            fp=fp,
        )

        corrientes = calcular_corrientes(corrientes_input)

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
            vmp_dc=paneles.array.vdc_nom,
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
            n_strings=paneles.array.n_strings_total,
        )

        protecciones = calcular_protecciones(entrada_prot)

        # ==================================================
        # RESULTADO FINAL
        # ==================================================
        return ResultadoElectrico.build(
            paneles=paneles,
            corrientes=corrientes,
            conductores=conductores,
            protecciones=protecciones,
        )

    except Exception as e:

        return ResultadoElectrico.build(
            paneles=paneles,
            corrientes=_corrientes_error(str(e)),
            conductores=_conductores_error(str(e)),
            protecciones=_protecciones_error(str(e)),
        )


# ==================================================
# HELPERS DE ERROR (CONSISTENTES)
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
