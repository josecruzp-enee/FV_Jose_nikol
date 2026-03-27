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
        # 2. PANELES (🔥 MULTIZONA CORRECTO)
        # --------------------------------------------------
        if not hasattr(datos, "sistema_fv"):
            raise ValueError("Datos sin sistema_fv")

        from core.aplicacion.builder_paneles import construir_entrada_paneles
        from core.aplicacion.multizona import ejecutar_multizona
        from electrical.paneles.entrada_panel import EntradaPaneles

        sf = getattr(datos, "sistema_fv", {})
        zonas = sf.get("zonas", [])

        if zonas:
            entradas = []

            for z in zonas:
                n_paneles = z.get("paneles", 0)

                if n_paneles <= 0:
                    continue

                entradas.append(
                    EntradaPaneles(
                        panel=sizing.panel,
                        inversor=sizing.inversor,
                        modo="manual",
                        n_paneles_total=n_paneles,
                        n_inversores=sizing.n_inversores,
                        t_min_c=getattr(sizing, "t_min_c", 25.0),
                        t_oper_c=getattr(sizing, "t_oper_c", 55.0),
                    )
                )

            paneles = ejecutar_multizona(entradas)

        else:
            entrada_paneles = construir_entrada_paneles(datos, sizing)
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

from electrical.resultado_electrical import ResultadoElectrico

def _ejecutar_electrical(datos, sizing, paneles, deps):

    if not deps.electrical:
        print("❌ ERROR: módulo electrical no configurado")
        return None

    try:
        resultado = deps.electrical.ejecutar(
            datos=datos,
            paneles=paneles,
            sizing=sizing,
        )

        if resultado is None:
            print("❌ ELECTRICAL devolvió None")

        return resultado

    except Exception:
        import traceback
        print("💥 ERROR EN ELECTRICAL:")
        print(traceback.format_exc())
        return None
def _ejecutar_finanzas(datos, sizing, energia, deps):

    if not deps.finanzas:
        return None

    return deps.finanzas.ejecutar(datos, sizing, energia)
