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
from dataclasses import replace

def _consolidar_paneles(resultados):

    if not resultados:
        return None

    base = resultados[0]

    strings = []
    total_strings = 0
    total_paneles = 0
    total_pdc = 0.0
    total_imp = 0.0
    total_isc = 0.0

    # ======================================================
    # CONSOLIDAR STRINGS (FIX CLAVE AQUÍ)
    # ======================================================
    for i, r in enumerate(resultados, 1):

        for s in r.strings:

            # 🔥 FIX: copiar objeto porque es frozen
            s_new = replace(s)

            object.__setattr__(s_new, "zona", i)
            object.__setattr__(s_new, "id_string", f"S{i}")

            strings.append(s_new)

        total_strings += len(r.strings)
        total_paneles += getattr(r.array, "n_paneles_total", 0)
        total_pdc += getattr(r.array, "potencia_dc_w", 0) / 1000.0
        total_imp += getattr(r.array, "idc_nom", 0)
        total_isc += getattr(r.array, "isc_total", 0)

    # ======================================================
    # ARRAY CONSOLIDADO
    # ======================================================
    array = type(base.array)(
        potencia_dc_w=total_pdc * 1000,
        vdc_nom=max(s.vmp_string_v for s in strings),  # FIX multizona
        idc_nom=total_imp,
        isc_total=total_isc,
        voc_frio_array_v=base.array.voc_frio_array_v,
        n_strings_total=total_strings,
        n_paneles_total=total_paneles,
        strings_por_mppt=base.array.strings_por_mppt,
        n_mppt=len(resultados),
        p_panel_w=base.array.p_panel_w,
    )

    # ======================================================
    # RESULTADO FINAL
    # ======================================================
    return type(base)(
        ok=True,
        strings=strings,
        array=array
    )
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
