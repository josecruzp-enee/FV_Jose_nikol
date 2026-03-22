from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional

from core.dominio.contrato import ResultadoProyecto

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
    PuertoFinanzas,
)


# ==========================================================
# DEPENDENCIAS
# ==========================================================

@dataclass
class DependenciasEstudio:
    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    nec: Optional[PuertoNEC] = None
    finanzas: PuertoFinanzas = None


# ==========================================================
# ORQUESTADOR
# ==========================================================

def ejecutar_estudio(
    datos: Any,
    deps: DependenciasEstudio,
):

    print("\n==============================")
    print("FV ENGINE — INICIO ESTUDIO")
    print("==============================")

    # ------------------------------------------------------
    # 1. SIZING
    # ------------------------------------------------------

    print("\n[1] EJECUTANDO SIZING")

    sizing = deps.sizing.ejecutar(datos)

    if getattr(sizing, "ok", True) is False:
        return asdict(ResultadoProyecto(
            sizing=sizing,
            strings=None,
            energia=None,
            nec=None,
            financiero=None,
        ))

    # ------------------------------------------------------
    # 2. PANELES / STRINGS
    # ------------------------------------------------------

    print("\n[2] EJECUTANDO PANEL / STRINGS")

    strings = deps.paneles.ejecutar(datos, sizing)

    print("\n--- DEBUG STRINGS ---")
    print(strings)
    print(getattr(strings, "strings", None))

    # ------------------------------------------------------
    # 3. ELÉCTRICO
    # ------------------------------------------------------

    print("\n[3] CALCULOS ELECTRICOS")

    from electrical.conductores.corrientes import calcular_corrientes, CorrientesInput
    from electrical.conductores.calculo_conductores import dimensionar_tramos_fv
    from electrical.protecciones.protecciones import calcular_protecciones, EntradaProtecciones

    if not hasattr(strings, "strings") or not strings.strings:

        print("⚠️ No hay strings → se omite cálculo eléctrico")

        corrientes = None
        conductores = None
        protecciones = None

    else:

        # -------------------------
        # CORRIENTES
        # -------------------------
        corrientes_input = CorrientesInput(
            paneles=strings,
            kw_ac=sizing.kw_ac,
            vac=240,
            fases=1,
            fp=1.0
        )

        corrientes = calcular_corrientes(corrientes_input)

        # -------------------------
        # CONDUCTORES
        # -------------------------
        conductores = dimensionar_tramos_fv(
            corrientes=corrientes,
            vmp_dc=600,
            vac=240,
            dist_dc_m=15,
            dist_ac_m=25,
            fases=1
        )

        # -------------------------
        # PROTECCIONES
        # -------------------------
        entrada_prot = EntradaProtecciones(
            corrientes=corrientes,
            n_strings=len(strings.strings)
        )

        protecciones = calcular_protecciones(entrada_prot)

        # -------------------------
        # DEBUG
        # -------------------------
        print("\n--- RESULTADOS ELÉCTRICOS ---")

        print("\n[CORRIENTES]")
        print(corrientes)

        print("\n[CONDUCTORES]")
        print(conductores)

        print("\n[PROTECCIONES]")
        print(protecciones)

    # ------------------------------------------------------
    # 4. ENERGÍA
    # ------------------------------------------------------

    print("\n[4] EJECUTANDO ENERGIA")

    energia = deps.energia.ejecutar(
        datos,
        sizing,
        strings,
    )

    # ------------------------------------------------------
    # 5. FINANZAS
    # ------------------------------------------------------

    print("\n[5] EJECUTANDO FINANZAS")

    financiero = deps.finanzas.ejecutar(
        datos,
        sizing,
        energia,
    )

    # ------------------------------------------------------
    # RESULTADO FINAL
    # ------------------------------------------------------

    resultado = ResultadoProyecto(
        sizing=sizing,
        strings=strings,
        energia=energia,
        nec={
            "corrientes": corrientes,
            "conductores": conductores,
            "protecciones": protecciones,
        },
        financiero=financiero,
    )

    print("\n==============================")
    print("FV ENGINE — FIN ESTUDIO")
    print("==============================")

    return resultado
