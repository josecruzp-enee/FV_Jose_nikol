from __future__ import annotations

from core.dominio.modelo import Datosproyecto
from core.dominio.contrato import ResultadoProyecto
from core.servicios.optimizacion_fv import optimizar_kwp_doble_escenario
from core.aplicacion.dependencias import DependenciasEstudio
from core.servicios.layout import construir_layout_preliminar_fv

# ==========================================================
# BATERÍAS
# ==========================================================
from energy.baterias import generar_opciones_bateria

# ==========================================================
# HELPERS BATERÍA
# ==========================================================

def _aplicar_bateria_si_corresponde(
    datos: Datosproyecto,
    sizing,
    paneles,
    energia,
):
    """
    Genera opciones técnicas de batería y las guarda en energia.
    Finanzas decidirá cuál opción conviene.
    """

    demanda_24h = getattr(
        datos,
        "consumo_horario_24h_kwh",
        {}
    ) or {}

    fv_24h = getattr(
        energia,
        "energia_horaria_kwh",
        None
    )

    if not demanda_24h or not fv_24h:
        return None

    opciones_bateria = generar_opciones_bateria(
        demanda_24h=demanda_24h,
        fv_24h=fv_24h,
        factor_aprovechamiento=0.80,
    )

    try:
        setattr(energia, "opciones_bateria", opciones_bateria)
    except Exception:
        pass

    return None
# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================
def ejecutar_estudio(
    datos: Datosproyecto,
    deps: DependenciasEstudio
) -> ResultadoProyecto:

    # ======================================================
    # Variables base
    # Importante: se inicializan para que no fallen
    # en modos distintos a optimización económica.
    # ======================================================
    sizing = None
    paneles = None
    energia = None
    bateria = None
    electrical = None
    finanzas = None
    optimizacion_economica = None
    layout_preliminar = None

    try:

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
                optimizacion_economica=None,
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
                optimizacion_economica=None,
                ok=False,
                errores=paneles.errores or ["Error en paneles"]
            )

        # ==================================================
        # 3. ENERGÍA BASE
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
                optimizacion_economica=None,
                ok=False,
                errores=energia.errores or ["Error en energía"]
            )

        # ==================================================
        # 3.0 BATERÍA BASE
        # ==================================================
        bateria = _aplicar_bateria_si_corresponde(
            datos=datos,
            sizing=sizing,
            paneles=paneles,
            energia=energia,
        )

        if bateria is not None and not bateria.ok:
            return ResultadoProyecto(
                sizing=sizing,
                paneles=paneles,
                strings=paneles.strings if paneles else None,
                energia=energia,
                electrical=None,
                financiero=None,
                optimizacion_economica=optimizacion_economica,
                ok=False,
                errores=bateria.errores or ["Error en batería"]
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

            energia_horaria = getattr(
                energia,
                "energia_horaria_kwh",
                None
            )

            if not energia_horaria:
                raise ValueError(
                    "Optimización económica requiere energia.energia_horaria_kwh."
                )

            panel_w = float(
                getattr(sizing.panel, "pmax_w", 0.0) or 0.0
            )

            if panel_w <= 0:
                raise ValueError(
                    "Potencia de panel inválida para optimización."
                )

            optimizacion_economica = optimizar_kwp_doble_escenario(
                demanda_24h=demanda_24h,
                energia_horaria_base_kwh=energia_horaria,
                pdc_kw_base=float(sizing.pdc_kw),
                panel_w=panel_w,
                tarifa_compra_l_kwh=float(
                    getattr(datos, "tarifa_energia", 0.0) or 0.0
                ),
                precio_inyeccion_l_kwh=2.20,
                costo_l_kwp=(
                    float(getattr(datos, "costo_usd_kwp", 1200.0) or 1200.0)
                    * float(getattr(datos, "tcambio", 26.61) or 26.61)
                ),
                tasa_descuento_anual=float(
                    getattr(datos, "tasa_anual", 0.10) or 0.10
                ),
                vida_util_anios=20,
                kwp_min=1.0,
                kwp_max=500.0,
                paso_kwp=1.0,
            )

            datos.sistema_fv["modo_original"] = "optimizacion_economica"
            datos.sistema_fv["modo"] = "kw_objetivo"
            escenario_base = optimizacion_economica["sin_inyeccion"]
            datos.sistema_fv["valor"] = float(escenario_base["pdc_kw"])
            datos.sistema_fv["optimizacion_economica"] = optimizacion_economica

            # ==================================================
            # Recalcular con tamaño óptimo
            # ==================================================
            sizing = deps.sizing.ejecutar(datos)

            if sizing is None:
                raise ValueError("Sizing optimizado devolvió None")

            if not sizing.ok:
                raise ValueError(
                    f"Sizing optimizado inválido: {sizing.errores}"
                )

            entrada_paneles = construir_entrada_paneles(datos, sizing)
            paneles = deps.paneles.ejecutar(entrada_paneles)

            if paneles is None:
                raise ValueError("Paneles optimizados devolvió None")

            if not paneles.ok:
                raise ValueError(
                    f"Paneles optimizados inválidos: {paneles.errores}"
                )

            energia = deps.energia.ejecutar(datos, sizing, paneles)

            if energia is None:
                raise ValueError("Energía optimizada devolvió None")

            if not energia.ok:
                raise ValueError(
                    f"Energía optimizada inválida: {energia.errores}"
                )

            # ==================================================
            # BATERÍA SOBRE ENERGÍA OPTIMIZADA
            # ==================================================
            bateria = _aplicar_bateria_si_corresponde(
                datos=datos,
                sizing=sizing,
                paneles=paneles,
                energia=energia,
            )

            if bateria is not None and not bateria.ok:
                return ResultadoProyecto(
                    sizing=sizing,
                    paneles=paneles,
                    strings=paneles.strings if paneles else None,
                    energia=energia,
                    electrical=None,
                    financiero=None,
                    optimizacion_economica=optimizacion_economica,
                    ok=False,
                    errores=bateria.errores or ["Error en batería"]
                )

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
                    optimizacion_economica=optimizacion_economica,
                    ok=False,
                    errores=electrical.errores or ["Error en electrical"]
                )

        # ==================================================
        # 5. FINANZAS
        # ==================================================
        finanzas = None

        if deps.finanzas is not None:

            finanzas = deps.finanzas.ejecutar(
                datos=datos,
                sizing=sizing,
                energia=energia,
                bateria=bateria,
        )

            if finanzas is None:
                raise ValueError("Finanzas devolvió None")

            if not getattr(finanzas, "ok", True):
                return ResultadoProyecto(
                    sizing=sizing,
                    paneles=paneles,
                    strings=paneles.strings if paneles else None,
                    energia=energia,
                    electrical=electrical,
                    financiero=finanzas,
                    optimizacion_economica=optimizacion_economica,
                    ok=False,
                    errores=getattr(
                        finanzas,
                        "errores",
                        ["Error en finanzas"]
                    )
                )

        # ==================================================
        # 5.1 LAYOUT PRELIMINAR FV
        # ==================================================
        panel = getattr(sizing, "panel", None)

        largo_panel_m = 2.20
        ancho_panel_m = 1.10

        if panel is not None:
            largo_mm = getattr(panel, "largo_mm", None)
            ancho_mm = getattr(panel, "ancho_mm", None)

            if largo_mm and ancho_mm:
                largo_panel_m = float(largo_mm) / 1000.0
                ancho_panel_m = float(ancho_mm) / 1000.0

        layout_preliminar = construir_layout_preliminar_fv(
            n_paneles=int(getattr(sizing, "n_paneles", 0) or 0),
            largo_panel_m=largo_panel_m,
            ancho_panel_m=ancho_panel_m,
            factor_ocupacion=0.75,
            separacion_x_m=0.20,
            separacion_y_m=0.40,
            max_columnas=None,
        )

        # ==================================================
        # RESULTADO FINAL
        # ==================================================
        return ResultadoProyecto(
            sizing=sizing,
            paneles=paneles,
            strings=paneles.strings,
            energia=energia,
            bateria=bateria,
            electrical=electrical,
            financiero=finanzas,
            layout_preliminar=layout_preliminar,
            optimizacion_economica=optimizacion_economica,
            ok=True,
            errores=[]
        )

    except Exception as e:

        import traceback
        print("💥 ERROR EN ORQUESTADOR:")
        print(traceback.format_exc())

        return ResultadoProyecto(
            sizing=sizing,
            paneles=paneles,
            strings=paneles.strings if paneles else None,
            energia=energia,
            bateria=bateria,
            electrical=electrical,
            financiero=finanzas,
            layout_preliminar=layout_preliminar,
            optimizacion_economica=optimizacion_economica,
            ok=False,
            errores=[str(e)]
        )
