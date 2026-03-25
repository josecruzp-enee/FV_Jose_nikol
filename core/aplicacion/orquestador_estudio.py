from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.dominio.contrato import ResultadoProyecto

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoEnergia,
    PuertoNEC,
    PuertoFinanzas,
)

from electrical.paneles.entrada_panel import EntradaPaneles
from core.aplicacion.multizona import ejecutar_multizona


# ==========================================================
# DEPENDENCIAS
# ==========================================================
@dataclass
class DependenciasEstudio:
    sizing: PuertoSizing
    paneles: PuertoPaneles
    energia: PuertoEnergia
    nec: Optional[PuertoNEC] = None
    finanzas: Optional[PuertoFinanzas] = None


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

    try:

        # ------------------------------------------------------
        # 1. SIZING
        # ------------------------------------------------------
        print("\n[1] EJECUTANDO SIZING")

        sizing = deps.sizing.ejecutar(datos)

        if sizing is None:
            raise ValueError("Sizing devolvió None")

        if getattr(sizing, "ok", True) is False:
            return ResultadoProyecto(
                sizing=sizing,
                strings=None,
                energia=None,
                nec=None,
                financiero=None,
            )

        # ------------------------------------------------------
        # 2. PANEL / STRINGS
        # ------------------------------------------------------
        print("\n[2] EJECUTANDO PANEL / STRINGS")

        # 🔥 IMPORTANTE: asegúrate que entrada_paneles exista arriba en tu código
        resultado_paneles = deps.paneles.ejecutar(entrada_paneles)

        if resultado_paneles is None:
            raise ValueError("Paneles devolvió None")

        if not resultado_paneles.ok:
            return ResultadoProyecto(
                sizing=sizing,
                strings=resultado_paneles,
                energia=None,
                nec=None,
                financiero=None,
            )

        # ------------------------------------------------------
        # 3. ENERGÍA
        # ------------------------------------------------------
        print("\n[3] EJECUTANDO ENERGIA")

        energia = deps.energia.ejecutar(
            datos,
            sizing,
            resultado_paneles,
        )

        if energia is None:
            raise ValueError("Energía devolvió None")

        if getattr(energia, "ok", True) is False:
            return ResultadoProyecto(
                sizing=sizing,
                strings=resultado_paneles,
                energia=energia,
                nec=None,
                financiero=None,
            )

        # ------------------------------------------------------
        # 4. ELECTRICAL (CORREGIDO)
        # ------------------------------------------------------
        print("\n[4] CALCULOS ELECTRICOS")

        resultado_electrico = None

        if deps.electrical:
            try:
                resultado_electrico = deps.electrical.ejecutar(
                    datos=datos,
                    paneles=resultado_paneles,
                    sizing=sizing,
                )

                if resultado_electrico is None:
                    raise ValueError("Electrical devolvió None")

            except Exception as e:
                print("🔥 ERROR ELECTRICAL:", str(e))
                resultado_electrico = None

        # ------------------------------------------------------
        # 5. FINANZAS
        # ------------------------------------------------------
        print("\n[5] EJECUTANDO FINANZAS")

        financiero = None

        if deps.finanzas:
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
            strings=resultado_paneles,
            energia=energia,
            nec=resultado_electrico,
            financiero=financiero,
        )

        print("\n==============================")
        print("FV ENGINE — FIN ESTUDIO")
        print("==============================")

        return resultado

    except Exception:

        import traceback

        print("\n🔥 ERROR REAL EN ORQUESTADOR 🔥")
        print(traceback.format_exc())

        raise
