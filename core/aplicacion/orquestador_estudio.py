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
from electrical.paneles.resultado_paneles import ResultadoPaneles
from electrical.catalogos.catalogos_yaml import get_inversor


def _consolidar_paneles(resultados, datos):

    print("\n🔧 CONSOLIDANDO PANELES")

    # ==================================================
    # VALIDACIÓN INICIAL
    # ==================================================
    if not resultados:
        raise ValueError("No hay resultados de paneles")

    if len(resultados) == 1:
        return resultados[0]

    # ==================================================
    # 🔥 OBTENER INVERSOR REAL
    # ==================================================
    inv_id = getattr(datos.equipos, "inversor_id", None)

    if not inv_id:
        print("⚠ No hay inversor definido → fallback MPPT por zonas")
        n_mppt_total = len(resultados)
    else:
        inv = get_inversor(inv_id)

        if not inv:
            print("⚠ Inversor no encontrado → fallback")
            n_mppt_total = len(resultados)
        else:
            n_mppt_total = max(1, int(inv.n_mppt))
            print(f"🔌 Inversor: {inv.modelo} | MPPT: {n_mppt_total}")

    # ==================================================
    # CONSOLIDAR STRINGS
    # ==================================================
    strings = []

    for i, r in enumerate(resultados, 1):

        print(f"\n🔹 ZONA {i}")

        for j, s in enumerate(r.strings, 1):

            s_new = replace(s)

            # zona (para UI)
            object.__setattr__(s_new, "zona", i)

            # 🔥 MPPT REAL (balanceado)
            mppt = (len(strings) % n_mppt_total) + 1
            object.__setattr__(s_new, "mppt", mppt)

            # id string
            object.__setattr__(s_new, "id_string", f"Z{i}_S{j}")

            print(f"  → String {j} → MPPT {mppt}")

            strings.append(s_new)

    # ==================================================
    # CONSOLIDAR ARRAY
    # ==================================================
    base = resultados[0]

    array_total = replace(base.array)

    total_potencia = sum(r.array.potencia_dc_w for r in resultados)
    total_strings = sum(r.array.n_strings_total for r in resultados)

    object.__setattr__(array_total, "potencia_dc_w", total_potencia)
    object.__setattr__(array_total, "n_strings_total", total_strings)

    print("\n📦 ARRAY CONSOLIDADO:")
    print("Potencia total (W):", total_potencia)
    print("Total strings:", total_strings)

    # ==================================================
    # RESULTADO FINAL
    # ==================================================
    return ResultadoPaneles(
        ok=True,
        topologia="string",
        panel=base.panel,
        array=array_total,
        strings=strings,
        warnings=[],
        errores=[]
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
