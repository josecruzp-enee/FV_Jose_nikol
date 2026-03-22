from __future__ import annotations

from typing import List

from electrical.conductores.corrientes import (
    calcular_corrientes,
    CorrientesInput,
    ResultadoCorrientes,
)

from electrical.protecciones.protecciones import (
    ejecutar_protecciones_fv,
    EntradaProteccionesFV,
    ProteccionesFVResultado,
)

from electrical.conductores.calculo_conductores import (
    tramo_conductor,
    TramosFV,
)

from electrical.resultado_electrical import ResultadoElectrical


# ==========================================================
# ORQUESTADOR ELÉCTRICO
# ==========================================================

def ejecutar_electrical(
    *,
    datos_strings,
    datos_inversor,
    n_strings: int,
    params_conductores
) -> ResultadoElectrical:

    errores: List[str] = []
    warnings: List[str] = []

    try:

        # --------------------------------------------------
        # 1. CORRIENTES
        # --------------------------------------------------

        corrientes: ResultadoCorrientes = calcular_corrientes(
            CorrientesInput(
                paneles=datos_strings,
                kw_ac=datos_inversor.kw_ac,
                vac=datos_inversor.v_ac_nom_v,
                fases=getattr(datos_inversor, "fases", 1),
                fp=getattr(datos_inversor, "fp", 1.0),
            )
        )

        # --------------------------------------------------
        # 2. PROTECCIONES
        # --------------------------------------------------

        protecciones: ProteccionesFVResultado = ejecutar_protecciones_fv(
            EntradaProteccionesFV(
                corrientes=corrientes,
                n_strings=n_strings
            )
        )

        # --------------------------------------------------
        # 3. CONDUCTORES
        # --------------------------------------------------

        tramo_dc = tramo_conductor(
            nombre="DC",
            i_diseno_a=corrientes.dc_total.i_diseno_a,
            v_base_v=params_conductores.vdc,
            l_m=params_conductores.l_dc,
            vd_obj_pct=params_conductores.vd_dc,
        )

        tramo_ac = tramo_conductor(
            nombre="AC",
            i_diseno_a=corrientes.ac.i_diseno_a,
            v_base_v=params_conductores.vac,
            l_m=params_conductores.l_ac,
            vd_obj_pct=params_conductores.vd_ac,
        )

        conductores = TramosFV(
            dc=tramo_dc,
            ac=tramo_ac
        )

        # --------------------------------------------------
        # RESULTADO FINAL
        # --------------------------------------------------

        return ResultadoElectrical(
            ok=True,
            errores=[],
            warnings=warnings,
            corrientes=corrientes,
            protecciones=protecciones,
            conductores=conductores,
        )

    except Exception as e:

        errores.append(str(e))

        return ResultadoElectrical(
            ok=False,
            errores=errores,
            warnings=warnings,
            corrientes=None,
            protecciones=None,
            conductores=None,
        )
