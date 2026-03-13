from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

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
    nec: PuertoNEC
    finanzas: PuertoFinanzas


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
    # 1. Dimensionamiento FV
    # ------------------------------------------------------

    sizing = deps.sizing.ejecutar(datos)

    print("\n[SIZING]")
    print("Tipo:", type(sizing))
    print("Contenido:", sizing)

    if getattr(sizing, "ok", True) is False:
        print("ERROR: sizing retornó ok=False")

        return asdict(ResultadoProyecto(
            sizing=sizing,
            strings=None,
            energia=None,
            nec=None,
            financiero=None,
        ))

    # ------------------------------------------------------
    # 2. Paneles / Strings
    # ------------------------------------------------------

    print("\n[PANELES] Ejecutando cálculo de strings...")

    strings = deps.paneles.ejecutar(
        datos,
        sizing,
    )

    print("[PANELES] Tipo:", type(strings))
    print("[PANELES] Resultado:", strings)

    if hasattr(strings, "strings"):
        print("[PANELES] n_strings_total:", getattr(strings, "n_strings_total", None))
        print("[PANELES] strings len:", len(strings.strings))
    else:
        print("[PANELES] WARNING: objeto no tiene atributo 'strings'")

    # ------------------------------------------------------
    # 3. Ingeniería eléctrica
    # ------------------------------------------------------

    print("\n[NEC] Ejecutando ingeniería eléctrica...")

    nec = deps.nec.ejecutar(
        datos,
        sizing,
        strings,
    )

    print("[NEC] Tipo:", type(nec))
    print("[NEC] Resultado:", nec)

    # ------------------------------------------------------
    # 4. Producción energética
    # ------------------------------------------------------

    print("\n[ENERGIA] Ejecutando simulación energética...")

    energia = deps.energia.ejecutar(
        datos,
        sizing,
        strings,
    )

    print("[ENERGIA] Tipo:", type(energia))
    print("[ENERGIA] Resultado:", energia)

    # ------------------------------------------------------
    # 5. Evaluación financiera
    # ------------------------------------------------------

    print("\n[FINANZAS] Ejecutando análisis financiero...")

    financiero = deps.finanzas.ejecutar(
        datos,
        sizing,
        energia,
    )

    print("[FINANZAS] Tipo:", type(financiero))
    print("[FINANZAS] Resultado:", financiero)

    # ------------------------------------------------------
    # Consolidación final
    # ------------------------------------------------------

    resultado = ResultadoProyecto(
        sizing=sizing,
        strings=strings,
        energia=energia,
        nec=nec,
        financiero=financiero,
    )

    print("\n==============================")
    print("FV ENGINE — FIN ESTUDIO")
    print("==============================")

    return resultado
