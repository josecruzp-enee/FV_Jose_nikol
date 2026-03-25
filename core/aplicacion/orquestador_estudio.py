from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import copy

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
    finanzas: Optional[PuertoFinanzas] = None


# ==========================================================
# 🔥 HELPER: INYECTAR INVERSOR REAL EN DATOS
# ==========================================================

def _inyectar_inversor_en_datos(datos, sizing):
    """
    Inyecta inversor y n_inversores en datos SIN romper estructura existente.
    """
    try:
        datos_fix = copy.deepcopy(datos)

        # 🔥 inyección estándar
        setattr(datos_fix, "inversor", sizing.inversor)
        setattr(datos_fix, "n_inversores", sizing.n_inversores)

        # opcional: algunos adapters usan esto
        if hasattr(datos_fix, "sistema"):
            setattr(datos_fix.sistema, "inversor", sizing.inversor)
            setattr(datos_fix.sistema, "n_inversores", sizing.n_inversores)

        return datos_fix

    except Exception as e:
        print("⚠ No se pudo inyectar inversor en datos:", str(e))
        return datos  # fallback seguro


# ==========================================================
# ORQUESTADOR
# ==========================================================

def ejecutar_estudio(
    datos: Any,
    deps: DependenciasEstudio,
) -> ResultadoProyecto:

    print("\n==============================")
    print("FV ENGINE — INICIO ESTUDIO")
    print("==============================")

    # ======================================================
    # 1. SIZING
    # ======================================================
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

    # ======================================================
    # 🔥 2. PREPARAR DATOS CORRECTOS PARA PANELES
    # ======================================================
    print("\n[2] PREPARANDO DATOS PARA PANELES")

    datos_paneles = _inyectar_inversor_en_datos(datos, sizing)

    print("DEBUG INYECCIÓN:")
    print(" - inversor:", getattr(datos_paneles, "inversor", None))
    print(" - n_inversores:", getattr(datos_paneles, "n_inversores", None))

    # ======================================================
    # 3. PANELES / STRINGS
    # ======================================================
    print("\n[3] EJECUTANDO PANEL / STRINGS")

    resultado_paneles = deps.paneles.ejecutar(datos_paneles, sizing)

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

    # ======================================================
    # 4. ELECTRICAL (NEC)
    # ======================================================
    print("\n[4] CALCULOS ELECTRICOS")

    resultado_electrico = None

    if deps.nec:
        try:
            resultado_electrico = deps.nec.ejecutar(
                datos=datos,
                paneles=resultado_paneles,
                sizing=sizing,
            )

            print("DEBUG ELECTRICAL:", resultado_electrico)

        except Exception as e:
            print("🔥 ERROR ELECTRICAL:", str(e))
            resultado_electrico = None

        if resultado_electrico is None:
            print("⚠ Electrical devolvió None")

        elif getattr(resultado_electrico, "ok", True) is False:
            print("⚠ Electrical con errores, se continúa flujo")

    # ======================================================
    # 5. ENERGÍA
    # ======================================================
    print("\n[5] EJECUTANDO ENERGIA")

    print("DEBUG INPUT ENERGIA:")
    print(" - sizing:", sizing)
    print(" - paneles:", resultado_paneles)

    energia = deps.energia.ejecutar(
        datos,
        sizing,
        resultado_paneles,
    )

    if energia is None:
        raise ValueError("Energía devolvió None")

    if not getattr(energia, "ok", True):
        raise ValueError(f"Energía inválida: {energia.errores}")

    # ======================================================
    # 6. FINANZAS
    # ======================================================
    print("\n[6] EJECUTANDO FINANZAS")

    financiero = None

    if deps.finanzas and energia is not None:
        try:
            financiero = deps.finanzas.ejecutar(
                datos,
                sizing,
                energia,
            )
        except Exception as e:
            print("🔥 ERROR FINANZAS:", str(e))
            financiero = None

    # ======================================================
    # RESULTADO FINAL
    # ======================================================
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
