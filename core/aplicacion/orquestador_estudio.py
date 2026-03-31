from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from core.dominio.contrato import ResultadoProyecto
from core.aplicacion.dependencias import DependenciasEstudio


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================

def ejecutar_estudio(datos: Any, deps: DependenciasEstudio) -> ResultadoProyecto:

    trazas = {}

    try:

        # ==================================================
        # 1. SIZING
        # ==================================================
        sizing = deps.sizing.ejecutar(datos)

        if sizing is None:
            raise ValueError("Sizing devolvió None")

        if not getattr(sizing, "ok", True):
            trazas["sizing"] = "FAIL"
            return ResultadoProyecto(
                sizing=sizing,
                paneles=None,
                energia=None,
                electrical=None,
                finanzas=None,
                trazas=trazas
            )

        trazas["sizing"] = "OK"

        # ==================================================
        # 2. PANELES
        # ==================================================
        from core.aplicacion.builder_paneles import construir_entrada_paneles

        entrada_paneles = construir_entrada_paneles(datos, sizing)

        paneles = deps.paneles.ejecutar(entrada_paneles)

        if paneles is None:
            raise ValueError("Paneles devolvió None")

        if not getattr(paneles, "ok", True):
            trazas["paneles"] = "FAIL"
            return ResultadoProyecto(
                sizing=sizing,
                paneles=paneles,
                energia=None,
                electrical=None,
                finanzas=None,
                trazas=trazas
            )

        trazas["paneles"] = "OK"

        # ==================================================
        # 3. ENERGÍA
        # ==================================================
        energia = deps.energia.ejecutar(datos, sizing, paneles)

        if energia is None:
            raise ValueError("Energía devolvió None")

        if not getattr(energia, "ok", True):
            trazas["energia"] = "FAIL"
            return ResultadoProyecto(
                sizing=sizing,
                paneles=paneles,
                energia=energia,
                electrical=None,
                finanzas=None,
                trazas=trazas
            )

        trazas["energia"] = "OK"

        # ==================================================
        # 4. ELECTRICAL
        # ==================================================
        electrical = None

        if deps.electrical:
            try:
                electrical = deps.electrical.ejecutar(
                    datos=datos,
                    paneles=paneles,
                    sizing=sizing
                )
                trazas["electrical"] = "OK" if electrical else "NONE"
            except Exception as e:
                trazas["electrical"] = f"ERROR: {str(e)}"
                electrical = None
        else:
            trazas["electrical"] = "NONE"

        # ==================================================
        # 5. FINANZAS
        # ==================================================
        finanzas = None

        if deps.finanzas:
            try:
                finanzas = deps.finanzas.ejecutar(
                    datos, sizing, energia
                )
                trazas["finanzas"] = "OK"
            except Exception as e:
                trazas["finanzas"] = f"ERROR: {str(e)}"
                finanzas = None
        else:
            trazas["finanzas"] = "NONE"

        # ==================================================
        # RESULTADO FINAL
        # ==================================================
        return ResultadoProyecto(
            ok=True,
            sizing=sizing,
            paneles=paneles,
            energia=energia,
            electrical=electrical,
            finanzas=finanzas,
            errores=[],
            warnings=[],
        )

    except Exception as e:

        return ResultadoProyecto(
            ok=False,
            sizing=None,
            paneles=None,
            energia=None,
            electrical=None,
            finanzas=None,
            errores=[str(e)],
            warnings=[],
        )
