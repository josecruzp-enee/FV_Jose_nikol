from __future__ import annotations

from electrical.paneles.resultado_paneles import ResultadoPaneles
from electrical.corrientes.calculo_corrientes import calcular_corrientes
from electrical.conductores.calculo_conductores import calcular_conductores
from electrical.protecciones.calculo_protecciones import calcular_protecciones
from electrical.protecciones.entrada_protecciones import EntradaProtecciones

from electrical.resultado_electrico import ResultadoElectrico


def ejecutar_electrical(
    *,
    paneles: ResultadoPaneles,
    params_conductores,
) -> ResultadoElectrico:
    """
    Orquestador principal del dominio electrical.
    Flujo obligatorio:
    paneles → corrientes → conductores → protecciones
    """

    try:

        # ==================================================
        # 1. VALIDAR PANELes
        # ==================================================

        if not paneles.ok:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=_corrientes_error("Paneles inválidos"),
                conductores=_conductores_error("Paneles inválidos"),
                protecciones=_protecciones_error("Paneles inválidos"),
            )

        # ==================================================
        # 2. CORRIENTES
        # ==================================================

        corrientes = calcular_corrientes(paneles)

        if not corrientes.ok:
            return ResultadoElectrico.build(
                paneles=paneles,
                corrientes=corrientes,
                conductores=_conductores_error("Corrientes inválidas"),
                protecciones=_protecciones_error("Corrientes inválidas"),
            )

        # ==================================================
        # 3. CONDUCTORES
        # ==================================================

        conductores = calcular_conductores(
            paneles=paneles,
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
        # 4. PROTECCIONES
        # ==================================================

        protecciones = calcular_protecciones(
            EntradaProtecciones(
                conductores=conductores,
                corrientes=corrientes,
            )
        )

        # ==================================================
        # 5. RESULTADO FINAL
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
# 🔧 HELPERS DE ERROR (OBLIGATORIO PARA CONSISTENCIA)
# ==================================================

def _corrientes_error(msg: str):
    from electrical.corrientes.resultado_corrientes import ResultadoCorrientes
    return ResultadoCorrientes.error(msg)


def _conductores_error(msg: str):
    from electrical.conductores.resultado_conductores import ResultadoConductores
    return ResultadoConductores.error(msg)


def _protecciones_error(msg: str):
    from electrical.protecciones.resultado_protecciones import ResultadoProtecciones
    return ResultadoProtecciones.error(msg)
