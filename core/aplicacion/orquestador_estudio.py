from __future__ import annotations

from typing import Any

from core.dominio.contrato import ResultadoProyecto
from core.aplicacion.dependencias import DependenciasEstudio


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================

def ejecutar_estudio(datos: Any, deps: DependenciasEstudio) -> ResultadoProyecto:

    try:

        # ==================================================
        # 1. SIZING
        # ==================================================
        sizing = deps.sizing.ejecutar(datos)

        if sizing is None:
            raise ValueError("Sizing devolvió None")

        if not getattr(sizing, "ok", True):
            return ResultadoProyecto(
                sizing=sizing,
                strings=None,
                energia=None,
                electrical=None,
                financiero=None,
                ok=False,
                errores=["Error en sizing"]
            )

        # ==================================================
        # 2. PANELES
        # ==================================================
        from core.aplicacion.builder_paneles import construir_entrada_paneles

        entrada_paneles = construir_entrada_paneles(datos, sizing)

        paneles = deps.paneles.ejecutar(entrada_paneles)

        if paneles is None:
            raise ValueError("Paneles devolvió None")

        if not getattr(paneles, "ok", True):
            return ResultadoProyecto(
                sizing=sizing,
                strings=paneles,
                energia=None,
                electrical=None,
                financiero=None,
                ok=False,
                errores=["Error en paneles"]
            )

        # ==================================================
        # 3. ENERGÍA
        # ==================================================
        energia = deps.energia.ejecutar(datos, sizing, paneles)

        if energia is None:
            raise ValueError("Energía devolvió None")

        if not getattr(energia, "ok", True):
            return ResultadoProyecto(
                sizing=sizing,
                strings=paneles,
                energia=energia,
                electrical=None,
                financiero=None,
                ok=False,
                errores=["Error en energía"]
            )

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
            except Exception:
                electrical = None

        # ==================================================
        # 5. FINANZAS
        # ==================================================
        finanzas = None

        if deps.finanzas:
            try:
                finanzas = deps.finanzas.ejecutar(
                    datos, sizing, energia
                )
            except Exception:
                finanzas = None

        # ==================================================
        # RESULTADO FINAL
        # ==================================================
        return ResultadoProyecto(
            sizing=sizing,
            strings=paneles,
            energia=energia,
            electrical=electrical,
            financiero=finanzas,
            ok=True,
            errores=[]
        )

    except Exception as e:

        return ResultadoProyecto(
            sizing=None,
            strings=None,
            energia=None,
            electrical=None,
            financiero=None,
            ok=False,
            errores=[str(e)]
        )
