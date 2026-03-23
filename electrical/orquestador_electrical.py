from __future__ import annotations

from electrical.paneles.resultado_paneles import ResultadoPaneles

from electrical.conductores.corrientes import (
    calcular_corrientes,
    CorrientesInput,
)

from electrical.conductores.calculo_conductores import (
    dimensionar_tramos_fv as calcular_conductores,
)

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
            kwargs["paneles"] = paneles
            kwargs["params_conductores"] = datos

    paneles = kwargs.get("paneles")
    params_conductores = kwargs.get("params_conductores")

    try:

        # ==================================================
        # VALIDACIÓN PANEL
        # ==================================================
        if not paneles or not paneles.ok:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=_corrientes_error("Paneles inválidos"),
                conductores=_conductores_error("Paneles inválidos"),
                protecciones=_protecciones_error("Paneles inválidos"),
            )

        # ==================================================
        # 🔥 EXTRAER PARAMETROS ELECTRICOS
        # ==================================================
        inst = getattr(params_conductores, "instalacion_electrica", None) or {}

        vac = inst.get("vac")
        fases = inst.get("fases")
        fp = inst.get("fp", 1.0)
        distancia_dc = inst.get("distancia_dc")
        distancia_ac = inst.get("distancia_ac")

        # ==================================================
        # VALIDACIÓN ELÉCTRICA
        # ==================================================
        if vac is None:
            raise ValueError("Falta 'vac' en instalacion_electrica")

        if fases is None:
            raise ValueError("Falta 'fases' en instalacion_electrica")

        # ==================================================
        # CORRIENTES
        # ==================================================
        corrientes_input = CorrientesInput(
            paneles=paneles,
            kw_ac=paneles.array.pdc_kw,
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
        # ⚠️ IMPORTANTE: si tu módulo espera atributos planos,
        # podés pasar params_conductores, pero ya sabés que viene con dict interno
        conductores = calcular_conductores(
            corrientes=corrientes,
            params=params_conductores,
        )

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
            conductores=conductores,
            corrientes=corrientes,
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
