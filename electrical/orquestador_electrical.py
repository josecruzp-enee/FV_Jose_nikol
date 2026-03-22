from __future__ import annotations

from typing import List

from electrical.paneles.resultado_paneles import ResultadoPaneles
from electrical.conductores.calculo_conductores import calcular_conductores
from electrical.protecciones.calculo_protecciones import calcular_protecciones
from electrical.protecciones.entrada_protecciones import EntradaProtecciones

from electrical.resultado_electrical import ResultadoElectrical


def ejecutar_electrical(
    *,
    paneles: ResultadoPaneles,
    params_conductores,
) -> ResultadoElectrical:

    errores: List[str] = []
    warnings: List[str] = []

    try:

        # ==================================================
        # 1. VALIDAR PANELes
        # ==================================================

        if not paneles.ok:
            return ResultadoElectrical(
                ok=False,
                errores=paneles.errores,
                warnings=paneles.warnings,
                paneles=paneles,
                conductores=None,
                protecciones=None,
            )

        # ==================================================
        # 2. CONDUCTORES (incluye NEC)
        # ==================================================

        conductores = calcular_conductores(
            paneles=paneles,
            params=params_conductores
        )

        # ==================================================
        # 3. PROTECCIONES
        # ==================================================

        protecciones = calcular_protecciones(
            EntradaProtecciones(conductores=conductores)
        )

        # ==================================================
        # RESULTADO FINAL
        # ==================================================

        errores.extend(conductores.errores)
        errores.extend(protecciones.errores)

        warnings.extend(conductores.warnings)
        warnings.extend(protecciones.warnings)

        return ResultadoElectrical(
            ok=len(errores) == 0,
            errores=errores,
            warnings=warnings,
            paneles=paneles,
            conductores=conductores,
            protecciones=protecciones,
        )

    except Exception as e:

        return ResultadoElectrical(
            ok=False,
            errores=[str(e)],
            warnings=[],
            paneles=paneles,
            conductores=None,
            protecciones=None,
        )
