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
def ejecutar_estudio(datos: Any, deps: DependenciasEstudio):

    trazas = {}

    try:
        # ==================================================
        # 1. SIZING
        # ==================================================
        try:
            sizing = _ejecutar_sizing(datos, deps)
            trazas["sizing"] = "OK"
        except Exception as e:
            trazas["sizing"] = f"ERROR: {str(e)}"
            return ResultadoProyecto(None, None, None, None, None, trazas)

        if not getattr(sizing, "ok", True):
            trazas["sizing"] = "FAIL"
            return ResultadoProyecto(sizing, None, None, None, None, trazas)

        # ==================================================
        # 2. PANELES
        # ==================================================
        try:
            from core.aplicacion.builder_paneles import construir_entrada_paneles
            entrada_paneles = construir_entrada_paneles(datos, sizing)
            paneles = _ejecutar_paneles(entrada_paneles, deps)
            trazas["paneles"] = "OK"
        except Exception as e:
            trazas["paneles"] = f"ERROR: {str(e)}"
            return ResultadoProyecto(sizing, None, None, None, None, trazas)

        if not getattr(paneles, "ok", True):
            trazas["paneles"] = "FAIL"
            return ResultadoProyecto(sizing, paneles, None, None, None, trazas)

        # ==================================================
        # 3. ENERGÍA
        # ==================================================
        try:
            energia = _ejecutar_energia(datos, sizing, paneles, deps)
            trazas["energia"] = "OK"
        except Exception as e:
            trazas["energia"] = f"ERROR: {str(e)}"
            return ResultadoProyecto(sizing, paneles, None, None, None, trazas)

        if not getattr(energia, "ok", True):
            trazas["energia"] = "FAIL"
            return ResultadoProyecto(sizing, paneles, energia, None, None, trazas)

        # ==================================================
        # 4. ELECTRICAL
        # ==================================================
        try:
            electrical = _ejecutar_electrical(datos, sizing, paneles, deps)
            trazas["electrical"] = "OK" if electrical else "NONE"
        except Exception as e:
            trazas["electrical"] = f"ERROR: {str(e)}"
            electrical = None

        # ==================================================
        # 5. FINANZAS
        # ==================================================
        try:
            financiero = _ejecutar_finanzas(datos, sizing, energia, deps)
            trazas["finanzas"] = "OK"
        except Exception as e:
            trazas["finanzas"] = f"ERROR: {str(e)}"
            financiero = None

        return ResultadoProyecto(
            sizing=sizing,
            strings=paneles,
            energia=energia,
            electrical=electrical,
            financiero=financiero,
            trazas=trazas,
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


# ==========================================================
# 🔥 ELECTRICAL (CLAVE)
# ==========================================================
def _ejecutar_electrical(datos, sizing, paneles, deps):

    try:
        print("\n⚡ [ELECTRICAL] INICIO")

        # 🔥 LLAMADA CORRECTA
        resultado = deps.electrical.ejecutar(
            datos=datos,
            paneles=paneles,
            sizing=sizing,   # 🔥 ESTE ERA EL PROBLEMA
        )

        if resultado is None:
            print("❌ ELECTRICAL devolvió None")
            return None

        # 🔍 DEBUG CONTROLADO
        print("\n⚡ [ELECTRICAL RESULTADO]")
        try:
            if hasattr(resultado, "corrientes"):
                print("corrientes:", resultado.corrientes)
            else:
                print(resultado)
        except:
            print("⚠ No se pudo imprimir corrientes")

        return resultado

    except Exception:
        import traceback
        print("💥 ERROR EN ELECTRICAL:")
        print(traceback.format_exc())
        return None
# ==========================================================
# FINANZAS
# ==========================================================
def _ejecutar_finanzas(datos, sizing, energia, deps):

    if not deps.finanzas:
        return None

    return deps.finanzas.ejecutar(datos, sizing, energia)
