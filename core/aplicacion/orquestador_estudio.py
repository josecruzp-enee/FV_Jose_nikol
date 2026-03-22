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
    nec: Optional[PuertoNEC] = None  # ✅ NEC ahora opcional
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
    # 2. PANELES / STRINGS
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
    # 3. NEC (OPCIONAL)
    # ------------------------------------------------------

    print("\n[3] EJECUTANDO NEC")

    nec = None

    if deps.nec is not None:

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

    else:
        print("NEC no implementado — se omite")

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

# ------------------------------------------------------
# 3. ELÉCTRICO (AQUÍ VA TODO)
# ------------------------------------------------------

print("\n[3] CALCULOS ELECTRICOS")

from electrical.conductores.corrientes import calcular_corrientes, CorrientesInput
from electrical.conductores.calculo_conductores import dimensionar_tramos_fv
from electrical.protecciones.protecciones import calcular_protecciones, EntradaProtecciones

corrientes_input = CorrientesInput(
    paneles=strings,
    kw_ac=sizing.kw_ac,
    vac=240,
    fases=1,
    fp=1.0
)

corrientes = calcular_corrientes(corrientes_input)

conductores = dimensionar_tramos_fv(
    corrientes=corrientes,
    vmp_dc=600,
    vac=240,
    dist_dc_m=20,
    dist_ac_m=20,
    fases=1
)

entrada_prot = EntradaProtecciones(
    corrientes=corrientes,
    n_strings=len(strings.strings) if hasattr(strings, "strings") else 1
)

protecciones = calcular_protecciones(entrada_prot)
