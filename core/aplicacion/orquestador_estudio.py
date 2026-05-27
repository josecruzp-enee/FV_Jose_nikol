from __future__ import annotations

from core.dominio.modelo import Datosproyecto
from core.dominio.contrato import ResultadoProyecto
from core.servicios.optimizacion_fv import optimizar_kwp_maximo_ahorro
from core.aplicacion.dependencias import DependenciasEstudio


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================
def ejecutar_estudio(
    datos: Datosproyecto,
    deps: DependenciasEstudio
) -> ResultadoProyecto:

    try:

        # ==================================================
        # VALIDACIÓN DE ENTRADA
        # ==================================================
        datos.validar_minimo()

        # ==================================================
        # 1. SIZING
        # ==================================================
        sizing = deps.sizing.ejecutar(datos)

        if sizing is None:
            raise ValueError("Sizing devolvió None")

        if not sizing.ok:
            return ResultadoProyecto(
                sizing=sizing,
                paneles=None,
                strings=None,
                energia=None,
                electrical=None,
                financiero=None,
                ok=False,
                errores=sizing.errores or ["Error en sizing"]
            )

        # ==================================================
        # 2. PANELES
        # ==================================================
        from core.aplicacion.builder_paneles import construir_entrada_paneles

        entrada_paneles = construir_entrada_paneles(datos, sizing)

        paneles = deps.paneles.ejecutar(entrada_paneles)

        if paneles is None:
            raise ValueError("Paneles devolvió None")

        if not paneles.ok:
            return ResultadoProyecto(
                sizing=sizing,
                paneles=paneles,
                strings=None,
                energia=None,
                electrical=None,
                financiero=None,
                ok=False,
                errores=paneles.errores or ["Error en paneles"]
            )

        # ==================================================
        # 3. ENERGÍA
        # ==================================================
        energia = deps.energia.ejecutar(datos, sizing, paneles)

        if energia is None:
            raise ValueError("Energía devolvió None")

        if not energia.ok:
            return ResultadoProyecto(
                sizing=sizing,
                paneles=paneles,
                strings=None,
                energia=energia,
                electrical=None,
                financiero=None,
                ok=False,
                errores=energia.errores or ["Error en energía"]
            )




                # ==================================================
        # 3.1 OPTIMIZACIÓN ECONÓMICA
        # ==================================================
        modo_sistema = getattr(datos, "sistema_fv", {}) or {}
        modo_actual = modo_sistema.get("modo")

        if modo_actual == "optimizacion_economica":

            demanda_24h = getattr(
                datos,
                "consumo_horario_24h_kwh",
                {}
            ) or {}

            if not demanda_24h:
                raise ValueError(
                    "Optimización económica requiere perfil horario de consumo."
                )

            panel_w = float(getattr(sizing.panel, "pmax_w", 0.0) or 0.0)

            if panel_w <= 0:
                raise ValueError("Potencia de panel inválida para optimización.")

            resultado_opt = optimizar_kwp_maximo_ahorro(
                demanda_24h=demanda_24h,
                energia_horaria_base_kwh=energia.energia_horaria_kwh,
                pdc_kw_base=float(sizing.pdc_kw),
                panel_w=panel_w,
                tarifa_compra_l_kwh=float(getattr(datos, "tarifa_energia", 0.0) or 0.0),
                precio_inyeccion_l_kwh=2.20,
                kwp_min=1.0,
                kwp_max=500.0,
                paso_kwp=1.0,
                mejora_minima_l_anual=1000.0,
            )

            datos.sistema_fv["modo"] = "kw_objetivo"
            datos.sistema_fv["valor"] = float(resultado_opt["pdc_kw"])
            datos.sistema_fv["optimizacion_economica"] = resultado_opt

            # Recalcular con tamaño óptimo
            sizing = deps.sizing.ejecutar(datos)

            entrada_paneles = construir_entrada_paneles(datos, sizing)
            paneles = deps.paneles.ejecutar(entrada_paneles)

            energia = deps.energia.ejecutar(datos, sizing, paneles)
            
        # ==================================================
        # 4. ELECTRICAL
        # ==================================================
        electrical = None

        if deps.electrical is not None:

            electrical = deps.electrical.ejecutar(
                datos=datos,
                paneles=paneles,
                sizing=sizing
            )

            if electrical is None:
                raise ValueError("Electrical devolvió None")

            if not electrical.ok:
                return ResultadoProyecto(
                    sizing=sizing,
                    paneles=paneles,
                    strings=paneles.strings,
                    energia=energia,
                    electrical=electrical,
                    financiero=None,
                    ok=False,
                    errores=electrical.errores or ["Error en electrical"]
                )

        # ==================================================
        # 5. FINANZAS
        # ==================================================
        finanzas = None

        if deps.finanzas is not None:

            finanzas = deps.finanzas.ejecutar(
                datos,
                sizing,
                energia
            )

            if finanzas is None:
                raise ValueError("Finanzas devolvió None")

            if not getattr(finanzas, "ok", True):
                return ResultadoProyecto(
                    sizing=sizing,
                    paneles=paneles,
                    strings=None,
                    energia=energia,
                    electrical=electrical,
                    financiero=finanzas,
                    ok=False,
                    errores=getattr(finanzas, "errores", ["Error en finanzas"])
                )

        # ==================================================
        # RESULTADO FINAL
        # ==================================================
        return ResultadoProyecto(
            sizing=sizing,
            paneles=paneles,
            strings=paneles.strings,
            energia=energia,
            electrical=electrical,
            financiero=finanzas,
            ok=True,
            errores=[]
        )

    except Exception as e:

        import traceback
        print("💥 ERROR EN ORQUESTADOR:")
        print(traceback.format_exc())

        return ResultadoProyecto(
            sizing=sizing if 'sizing' in locals() else None,
            paneles=paneles if 'paneles' in locals() else None,
            strings=paneles.strings if 'paneles' in locals() and paneles else None,
            energia=energia if 'energia' in locals() else None,
            electrical=electrical if 'electrical' in locals() else None,
            financiero=finanzas if 'finanzas' in locals() else None,
            ok=False,
            errores=[str(e)]
        )
