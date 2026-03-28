from __future__ import annotations

from dataclasses import dataclass, replace
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
        # 2. PANELES (🔥 MULTIZONA INTEGRADO)
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


# ==========================================================
# 🔥 PANEL (MULTIZONA AQUÍ)
# ==========================================================
def _ejecutar_paneles(entrada_paneles, deps):

    # ------------------------------------------------------
    # 🔥 MULTIZONA
    # ------------------------------------------------------
    if getattr(entrada_paneles, "modo", None) == "multizona":

        zonas = getattr(entrada_paneles, "zonas", []) or []

        if not zonas:
            raise ValueError("Modo multizona sin zonas definidas")

        resultados = []

        for i, zona in enumerate(zonas):

            entrada_zona = _clonar_entrada_para_zona(
                entrada_paneles,
                n_paneles=zona.get("n_paneles")
            )

            resultado = deps.paneles.ejecutar(entrada_zona)

            if resultado is None:
                raise ValueError(f"Paneles devolvió None en zona {i+1}")

            if not getattr(resultado, "ok", False):
                return resultado

            resultados.append(resultado)

        return _consolidar_paneles(resultados)

    # ------------------------------------------------------
    # 🔹 NORMAL
    # ------------------------------------------------------
    resultado = deps.paneles.ejecutar(entrada_paneles)

    if resultado is None:
        raise ValueError("Paneles devolvió None")

    return resultado


# ==========================================================
# CLONADOR ZONA
# ==========================================================
def _clonar_entrada_para_zona(entrada, n_paneles):

    return replace(
        entrada,
        n_paneles_total=int(n_paneles or 0),
        modo="manual",   # evita recursión
        zonas=None
    )


# ==========================================================
# CONSOLIDADOR
# ==========================================================
def _consolidar_paneles(resultados):

    base = resultados[0]

    total_paneles = sum(r.meta.n_paneles_total for r in resultados)
    total_pdc = sum(r.meta.pdc_kw for r in resultados)
    total_strings = sum(r.array.n_strings_total for r in resultados)

    total_imp = sum(s.imp_string_a for r in resultados for s in r.strings)
    total_isc = sum(s.isc_string_a for r in resultados for s in r.strings)

    # 🔥 ARRAY
    base.array.n_paneles_total = total_paneles
    base.array.n_strings_total = total_strings
    base.array.potencia_dc_w = total_pdc * 1000
    base.array.idc_nom = total_imp
    base.array.isc_total = total_isc

    # 🔥 META
    base.meta.n_paneles_total = total_paneles
    base.meta.pdc_kw = total_pdc

    # 🔥 STRINGS
    base.strings = [s for r in resultados for s in r.strings]

    # 🔥 WARNINGS
    base.warnings = [w for r in resultados for w in r.warnings]
    print("TOTAL PANELES:", base.meta.n_paneles_total)
    print("TOTAL STRINGS:", base.array.n_strings_total)
    return base


# ==========================================================
# ENERGÍA
# ==========================================================
def _ejecutar_energia(datos, sizing, paneles, deps):
    energia = deps.energia.ejecutar(datos, sizing, paneles)

    if energia is None:
        raise ValueError("Energía devolvió None")

    return energia


# ==========================================================
# ELECTRICAL
# ==========================================================
def _ejecutar_electrical(datos, sizing, paneles, deps):

    try:
        print("\n⚡ [ELECTRICAL] INICIO")

        resultado = deps.electrical.ejecutar(
            datos=datos,
            paneles=paneles,
            sizing=sizing,
        )

        if resultado is None:
            print("❌ ELECTRICAL devolvió None")
            return None

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
