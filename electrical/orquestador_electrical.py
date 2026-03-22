from __future__ import annotations

from dataclasses import dataclass
from typing import List

from electrical.conductores.corrientes import (
    calcular_corrientes,
    CorrientesInput,
)
from electrical.protecciones.protecciones import (
    ejecutar_protecciones_fv,
    EntradaProteccionesFV,
)
from electrical.conductores.calculo_conductores import tramo_conductor
from electrical.conductores.corrientes import ResultadoCorrientes

# ==========================================================
# RESULTADO GLOBAL
# ==========================================================

@dataclass(frozen=True)
class ResultadoElectrico:

    ok: bool
    errores: List[str]
    warnings: List[str]

    corrientes: ResultadoCorrientes
    protecciones: object
    conductores: list


# ==========================================================
# ORQUESTADOR
# ==========================================================

def ejecutar_ingenieria_electrica(
    *,
    datos_strings,
    datos_inversor,
    n_strings: int,
    params_conductores
) -> ResultadoElectrico:

    errores: List[str] = []
    warnings: List[str] = []

    try:

        # --------------------------------------------------
        # 1. CORRIENTES (CORREGIDO)
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

        protecciones = ejecutar_protecciones_fv(
            EntradaProteccionesFV(
                corrientes=corrientes,
                n_strings=n_strings
            )
        )

        # --------------------------------------------------
        # 3. CONDUCTORES
        # --------------------------------------------------

        conductores = []

        # DC
        conductores.append(
            tramo_conductor(
                nombre="DC",
                i_diseno_a=corrientes.dc_total.i_diseno_a,
                v_base_v=params_conductores.vdc,
                l_m=params_conductores.l_dc,
                vd_obj_pct=params_conductores.vd_dc,
            )
        )

        # AC
        conductores.append(
            tramo_conductor(
                nombre="AC",
                i_diseno_a=corrientes.ac.i_diseno_a,
                v_base_v=params_conductores.vac,
                l_m=params_conductores.l_ac,
                vd_obj_pct=params_conductores.vd_ac,
            )
        )

        # --------------------------------------------------
        # RESULTADO
        # --------------------------------------------------

        return ResultadoElectrico(
            ok=True,
            errores=[],
            warnings=warnings,
            corrientes=corrientes,
            protecciones=protecciones,
            conductores=conductores,
        )

    except Exception as e:

        errores.append(str(e))

        return ResultadoElectrico(
            ok=False,
            errores=errores,
            warnings=warnings,
            corrientes=None,
            protecciones=None,
            conductores=[],
        )
