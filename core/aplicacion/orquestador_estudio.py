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


@dataclass
class DependenciasEstudio:

    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    nec: PuertoNEC
    finanzas: PuertoFinanzas

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

    print("TYPE sizing:", type(sizing))
    print("VALUE sizing:", sizing)

    if getattr(sizing, "ok", True) is False:

        print("ERROR: sizing retornó ok=False")

        return asdict(ResultadoProyecto(
            sizing=sizing,
            strings=None,
            energia=None,
            nec=None,
            financiero=None,
        ))

    print("n_paneles:", getattr(sizing, "n_paneles", None))
    print("n_inversores:", getattr(sizing, "n_inversores", None))

    # ------------------------------------------------------
    # 2. PANELES
    # ------------------------------------------------------

    print("\n[2] EJECUTANDO PANEL / STRINGS")

    strings = deps.paneles.ejecutar(
        datos,
        sizing,
    )

    print("\n--- RESULTADO PANEL ---")
    print("TYPE:", type(strings))
    print("RAW VALUE:", strings)

    if isinstance(strings, dict):

        print("DICT DETECTADO")

        print("KEYS:", list(strings.keys()))

        if "strings" in strings:

            lista = strings["strings"]

            print("strings len:", len(lista))

            if len(lista) > 0:
                print("primer string:", lista[0])

        else:

            print("NO EXISTE CLAVE 'strings'")

    elif hasattr(strings, "strings"):

        print("DATACLASS DETECTADA")

        print("n_strings_total:", getattr(strings, "n_strings_total", None))

        print("strings len:", len(strings.strings))

        if strings.strings:
            print("primer string:", strings.strings[0])

    else:

        print("FORMATO DESCONOCIDO")

    # ------------------------------------------------------
    # 3. NEC
    # ------------------------------------------------------

    print("\n[3] EJECUTANDO NEC")

    try:

        nec = deps.nec.ejecutar(
            datos,
            sizing,
            strings,
        )

        print("NEC TYPE:", type(nec))
        print("NEC VALUE:", nec)

    except Exception as e:

        print("\n*** ERROR EN NEC ***")
        print("EXCEPTION:", e)
        raise

    # ------------------------------------------------------
    # 4. ENERGÍA
    # ------------------------------------------------------

    print("\n[4] EJECUTANDO ENERGIA")

    energia = deps.energia.ejecutar(
        datos,
        sizing,
        strings,
    )

    print("ENERGIA TYPE:", type(energia))
    print("ENERGIA VALUE:", energia)

    # ------------------------------------------------------
    # 5. FINANZAS
    # ------------------------------------------------------

    print("\n[5] EJECUTANDO FINANZAS")

    financiero = deps.finanzas.ejecutar(
        datos,
        sizing,
        energia,
    )

    print("FINANZAS TYPE:", type(financiero))
    print("FINANZAS VALUE:", financiero)

    # ------------------------------------------------------
    # RESULTADO FINAL
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
