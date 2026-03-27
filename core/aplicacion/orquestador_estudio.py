from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.dominio.contrato import ResultadoProyecto

from core.aplicacion.puertos import (
    PuertoSizing,
    PuertoPaneles,
    PuertoElectrical,
    PuertoEnergia,
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
    electrical: Optional[PuertoElectrical]
    finanzas: Optional[PuertoFinanzas] = None


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================
def _ejecutar_electrical(datos, sizing, paneles, deps):

    if not deps.electrical:
        print("⚠ No hay módulo electrical")
        return None

    print("🔥 LLAMANDO ELECTRICAL")

    resultado = deps.electrical.ejecutar(
        datos=datos,
        paneles=paneles,
        sizing=sizing,
    )

    print("⚡ RESULTADO ELECTRICAL:", resultado)
    print("⚡ TIPO:", type(resultado))

    if resultado is None:
        print("❌ ELECTRICAL DEVOLVIÓ NONE")

    return resultado
        # --------------------------------------------------
        # 3. ENERGÍA
        # --------------------------------------------------
        energia = _ejecutar_energia(datos, sizing, paneles, deps)

        if not getattr(energia, "ok", True):
            return ResultadoProyecto(
                sizing=sizing,
                strings=paneles,
                energia=energia,
                electrical=None,
                financiero=None
            )

        # --------------------------------------------------
        # 4. ELECTRICAL
        # --------------------------------------------------
        electrico = _ejecutar_electrical(datos, sizing, paneles, deps)

        # --------------------------------------------------
        # 5. FINANZAS
        # --------------------------------------------------
        financiero = _ejecutar_finanzas(datos, sizing, energia, deps)

        # --------------------------------------------------
        # RESULTADO FINAL
        # --------------------------------------------------
        return ResultadoProyecto(
            sizing=sizing,
            strings=paneles,
            energia=energia,
            electrical=electrico,
            financiero=financiero,
        )

    except Exception:
        import traceback
        print(traceback.format_exc())
        raise
# ==========================================================
# FUNCIONES INTERNAS
# ==========================================================

def _ejecutar_sizing(datos, deps):
    sizing = deps.sizing.ejecutar(datos)

    if sizing is None:
        raise ValueError("Sizing devolvió None")

    return sizing


def _ejecutar_paneles(entrada_paneles, deps):

    resultado = deps.paneles.ejecutar(entrada_paneles)

    if resultado is None:
        raise ValueError("Paneles devolvió None")

    return resultado


def _ejecutar_energia(datos, sizing, paneles, deps):

    energia = deps.energia.ejecutar(datos, sizing, paneles)

    if energia is None:
        raise ValueError("Energía devolvió None")

    return energia


def _ejecutar_electrical(datos, sizing, paneles, deps):

    if not deps.electrical:
        print("⚠ No hay módulo electrical")
        return None

    print("🔥 LLAMANDO ELECTRICAL")

    resultado = deps.electrical.ejecutar(
        datos=datos,
        paneles=paneles,
        sizing=sizing,
    )

    print("⚡ RESULTADO ELECTRICAL:", resultado)

    return resultado


def _ejecutar_finanzas(datos, sizing, energia, deps):

    if not deps.finanzas:
        return None

    return deps.finanzas.ejecutar(datos, sizing, energia)
