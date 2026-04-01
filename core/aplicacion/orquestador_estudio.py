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
        # 2. PANELES / STRINGS
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
        # 4. ELECTRICAL (CRÍTICO)
        # ==================================================
        electrical = None

        if deps.electrical:

            electrical = deps.electrical.ejecutar(
                datos=datos,
                paneles=paneles,
                sizing=sizing
            )

            if electrical is None:
                raise ValueError("Electrical devolvió None")

            if not getattr(electrical, "ok", True):
                return ResultadoProyecto(
                    sizing=sizing,
                    strings=paneles,
                    energia=energia,
                    electrical=electrical,
                    financiero=None,
                    ok=False,
                    errores=["Error en electrical"]
                )

        # ==================================================
        # 5. FINANZAS
        # ==================================================
        finanzas = None

        if deps.finanzas:

            finanzas = deps.finanzas.ejecutar(
                datos,
                sizing,
                energia
            )

            if finanzas is None:
                raise ValueError("Finanzas devolvió None")

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

        # 🔥 DEBUG REAL (NO OCULTAR ERROR)
        import traceback
        print(traceback.format_exc())

        return ResultadoProyecto(
            sizing=None,
            strings=None,
            energia=None,
            electrical=None,
            financiero=None,
            ok=False,
            errores=[str(e)]
        )
