from __future__ import annotations

from electrical.paneles.resultado_paneles import ResultadoPaneles

from electrical.conductores.corrientes import (
    calcular_corrientes,
    CorrientesInput,
)

from electrical.conductores.calculo_conductores import dimensionar_tramos_fv as calcular_conductores
from electrical.conductores.resultado_conductores import ResultadoConductores

from electrical.protecciones.protecciones import calcular_protecciones
from electrical.protecciones.protecciones import EntradaProtecciones

from electrical.resultado_electrico import ResultadoElectrico


def ejecutar_electrical(
    *,
    paneles: ResultadoPaneles,
    params_conductores,
) -> ResultadoElectrico:
    """
    Orquestador principal del dominio electrical.

    Flujo:
        paneles → corrientes → conductores → protecciones
    """

    try:

        # ==================================================
        # 1. VALIDACIÓN INICIAL
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

        corrientes_input = CorrientesInput(
            paneles=paneles,
            kw_ac=paneles.array.pdc_kw,   # ajustar si cambias modelo
            vac=params_conductores.vac,
            fases=params_conductores.fases,
            fp=1.0,
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
        # 3. CONDUCTORES
        # ==================================================

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
        # 4. PROTECCIONES
        # ==================================================

        entrada_prot = EntradaProtecciones(
            conductores=conductores,
            corrientes=corrientes,
        )

        protecciones = calcular_protecciones(entrada_prot)

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
# HELPERS DE ERROR (CONSISTENTES EN TODO EL SISTEMA)
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
