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

    print("\n🔥 ===============================")
    print("🔥 LLAMANDO ELECTRICAL")
    print("🔥 datos:", type(datos))
    print("🔥 sizing kw_ac:", getattr(sizing, "kw_ac", None))
    print("🔥 paneles ok:", getattr(paneles, "ok", None))
    print("🔥 paneles strings:", len(getattr(paneles, "strings", [])))
    print("🔥 paneles array:", getattr(paneles, "array", None))

    try:
        resultado = deps.electrical.ejecutar(
            datos=datos,
            paneles=paneles,
            sizing=sizing,
        )

        print("⚡ RESULTADO ELECTRICAL:", resultado)
        print("⚡ TIPO:", type(resultado))

        if resultado is None:
            print("❌ ELECTRICAL DEVOLVIÓ NONE")
        else:
            print("✅ ELECTRICAL OK:", getattr(resultado, "ok", None))

        print("🔥 ===============================\n")

        return resultado

    except Exception as e:
        import traceback
        print("💥 ERROR EN ELECTRICAL:")
        print(traceback.format_exc())
        return None
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
