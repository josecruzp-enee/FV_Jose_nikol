from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, List

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
        # 2. PANELES (🔥 MULTIZONA READY)
        # --------------------------------------------------
        from core.aplicacion.helpers_zonas import extraer_zonas
        from core.aplicacion.builder_paneles import (
            construir_entrada_paneles,
            construir_entrada_panel_desde_zona,
        )

        zonas = extraer_zonas(datos)

        # =========================
        # CASO LEGACY (1 zona)
        # =========================
        if len(zonas) == 1:

            entrada_paneles = construir_entrada_paneles(
                datos,
                sizing,
            )

            paneles = _ejecutar_paneles(entrada_paneles, deps)

            if not paneles.ok:
                return ResultadoProyecto(
                    sizing=sizing,
                    strings=paneles,
                    energia=None,
                    electrical=None,
                    financiero=None
                )

        # =========================
        # CASO MULTIZONA
        # =========================
        else:

            resultados_zonas: List[Any] = []

            for z in zonas:

                entrada = construir_entrada_panel_desde_zona(
                    z,
                    sizing,
                )

                res = _ejecutar_paneles(entrada, deps)

                if not getattr(res, "ok", True):
                    return ResultadoProyecto(
                        sizing=sizing,
                        strings=res,
                        energia=None,
                        electrical=None,
                        financiero=None
                    )

                resultados_zonas.append(res)

            # 👉 dejamos lista (no consolidamos aquí)
            paneles = resultados_zonas

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
