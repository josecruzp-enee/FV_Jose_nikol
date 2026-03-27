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

    try:
        # --------------------------------------------------
        # 1. SIZING
        # --------------------------------------------------
        sizing = _ejecutar_sizing(datos, deps)

        if not getattr(sizing, "ok", True):
            return ResultadoProyecto(
                sizing=sizing,
                strings=None,
                energia=None,
                electrical=None,
                financiero=None
            )

        # --------------------------------------------------
        # 2. PANELES
        # --------------------------------------------------
        if not hasattr(datos, "sistema_fv"):
            raise ValueError("Datos sin sistema_fv")

        from core.aplicacion.builder_paneles import construir_entrada_paneles

        entrada_paneles = construir_entrada_paneles(
            sf=datos.sistema_fv,
            panel=sizing.panel,
            inversor=sizing.inversor,
            n_inversores=sizing.n_inversores,
            t_min=getattr(sizing, "t_min_c", 25.0),
            t_oper=getattr(sizing, "t_oper_c", 55.0),
        )

        paneles = _ejecutar_paneles(entrada_paneles, deps)

        if not getattr(paneles, "ok", True):
            return ResultadoProyecto(
                sizing=sizing,
                strings=paneles,
                energia=None,
                electrical=None,
                financiero=None
            )

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
        electrical = _ejecutar_electrical(datos, sizing, paneles, deps)

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
            electrical=electrical,
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


# 🔥 CON DEBUG (CLAVE PARA DIAGNÓSTICO)
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


def _ejecutar_finanzas(datos, sizing, energia, deps):

    if not deps.finanzas:
        return None

    return deps.finanzas.ejecutar(datos, sizing, energia)
