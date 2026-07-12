from __future__ import annotations

import traceback

from core.aplicacion.builder_paneles import construir_entrada_paneles
from core.aplicacion.dependencias import DependenciasEstudio
from core.dominio.contrato import ResultadoProyecto
from core.dominio.modelo import Datosproyecto
from core.servicios.layout import construir_layout_preliminar_fv
from core.servicios.optimizacion_fv import (
    optimizar_kwp_doble_escenario,
)
from energy.baterias.orquestador_bateria import (
    ejecutar_recomendacion_bateria,
)


# ==========================================================
# VALIDACIONES
# ==========================================================

def _validar_resultado(resultado, nombre: str) -> None:

    if resultado is None:
        raise ValueError(f"{nombre} devolvió None")

    if not getattr(resultado, "ok", True):
        errores = getattr(
            resultado,
            "errores",
            [f"Error en {nombre}"],
        )

        raise ValueError(
            f"{nombre} inválido: {errores}"
        )


# ==========================================================
# ETAPAS PRINCIPALES
# ==========================================================

def _ejecutar_sizing(
    datos: Datosproyecto,
    deps: DependenciasEstudio,
):

    sizing = deps.sizing.ejecutar(datos)
    _validar_resultado(sizing, "Sizing")

    return sizing


def _ejecutar_paneles(
    datos: Datosproyecto,
    sizing,
    deps: DependenciasEstudio,
):

    entrada = construir_entrada_paneles(
        datos,
        sizing,
    )

    paneles = deps.paneles.ejecutar(entrada)
    _validar_resultado(paneles, "Paneles")

    return paneles


def _ejecutar_energia(
    datos: Datosproyecto,
    sizing,
    paneles,
    deps: DependenciasEstudio,
):

    energia = deps.energia.ejecutar(
        datos,
        sizing,
        paneles,
    )

    _validar_resultado(energia, "Energía")

    return energia


def _ejecutar_electrical(
    datos: Datosproyecto,
    sizing,
    paneles,
    deps: DependenciasEstudio,
):

    if deps.electrical is None:
        return None

    electrical = deps.electrical.ejecutar(
        datos=datos,
        paneles=paneles,
        sizing=sizing,
    )

    _validar_resultado(
        electrical,
        "Electrical",
    )

    return electrical


# ==========================================================
# BATERÍAS
# ==========================================================

def _aplicar_bateria_si_corresponde(
    datos: Datosproyecto,
    energia,
) -> None:

    demanda_24h = getattr(
        datos,
        "consumo_horario_24h_kwh",
        {},
    ) or {}

    energia_horaria = getattr(
        energia,
        "energia_horaria_kwh",
        None,
    )

    if not demanda_24h or not energia_horaria:
        return

    opciones = ejecutar_recomendacion_bateria(
        demanda_24h=demanda_24h,
        fv_24h=energia_horaria,
        factor_aprovechamiento=0.80,
    )

    setattr(
        energia,
        "opciones_bateria",
        opciones,
    )

    if opciones:
        setattr(
            energia,
            "bateria_recomendada",
            opciones[-1],
        )


def _extraer_bateria_seleccionada(finanzas):

    if not isinstance(finanzas, dict):
        return None

    bateria_optima = (
        finanzas.get("bateria_optima")
        or {}
    )

    return bateria_optima.get(
        "resultado_bateria"
    )


# ==========================================================
# OPTIMIZACIÓN FV
# ==========================================================

def _requiere_optimizacion(
    datos: Datosproyecto,
) -> bool:

    sistema_fv = getattr(
        datos,
        "sistema_fv",
        {},
    ) or {}

    return (
        sistema_fv.get("modo")
        == "optimizacion_economica"
    )


def _calcular_optimizacion(
    datos: Datosproyecto,
    sizing,
    energia,
):

    demanda_24h = getattr(
        datos,
        "consumo_horario_24h_kwh",
        {},
    ) or {}

    if not demanda_24h:
        raise ValueError(
            "Optimización económica requiere "
            "perfil horario de consumo."
        )

    energia_horaria = getattr(
        energia,
        "energia_horaria_kwh",
        None,
    )

    if not energia_horaria:
        raise ValueError(
            "Optimización económica requiere "
            "energia.energia_horaria_kwh."
        )

    panel = getattr(sizing, "panel", None)

    panel_w = float(
        getattr(panel, "pmax_w", 0.0)
        or 0.0
    )

    if panel_w <= 0:
        raise ValueError(
            "Potencia de panel inválida "
            "para optimización."
        )

    costo_l_kwp = (
        float(
            getattr(
                datos,
                "costo_usd_kwp",
                1200.0,
            )
            or 1200.0
        )
        * float(
            getattr(
                datos,
                "tcambio",
                26.61,
            )
            or 26.61
        )
    )

    return optimizar_kwp_doble_escenario(
        demanda_24h=demanda_24h,
        energia_horaria_base_kwh=energia_horaria,
        pdc_kw_base=float(sizing.pdc_kw),
        panel_w=panel_w,
        tarifa_compra_l_kwh=float(
            getattr(
                datos,
                "tarifa_energia",
                0.0,
            )
            or 0.0
        ),
        precio_inyeccion_l_kwh=2.20,
        costo_l_kwp=costo_l_kwp,
        tasa_descuento_anual=float(
            getattr(
                datos,
                "tasa_anual",
                0.10,
            )
            or 0.10
        ),
        vida_util_anios=20,
        kwp_min=1.0,
        kwp_max=500.0,
        paso_kwp=1.0,
    )


def _aplicar_resultado_optimizacion(
    datos: Datosproyecto,
    optimizacion_economica,
) -> None:

    escenario = optimizacion_economica[
        "sin_inyeccion"
    ]

    datos.sistema_fv[
        "modo_original"
    ] = "optimizacion_economica"

    datos.sistema_fv["modo"] = "kw_objetivo"

    datos.sistema_fv["valor"] = float(
        escenario["pdc_kw"]
    )

    datos.sistema_fv[
        "optimizacion_economica"
    ] = optimizacion_economica


def _optimizar_y_recalcular(
    datos: Datosproyecto,
    sizing,
    energia,
    deps: DependenciasEstudio,
):

    optimizacion = _calcular_optimizacion(
        datos,
        sizing,
        energia,
    )

    _aplicar_resultado_optimizacion(
        datos,
        optimizacion,
    )

    sizing = _ejecutar_sizing(
        datos,
        deps,
    )

    paneles = _ejecutar_paneles(
        datos,
        sizing,
        deps,
    )

    energia = _ejecutar_energia(
        datos,
        sizing,
        paneles,
        deps,
    )

    return (
        sizing,
        paneles,
        energia,
        optimizacion,
    )


# ==========================================================
# FINANZAS
# ==========================================================

def _ejecutar_finanzas(
    datos: Datosproyecto,
    sizing,
    energia,
    deps: DependenciasEstudio,
):

    if deps.finanzas is None:
        return None

    finanzas = deps.finanzas.ejecutar(
        datos=datos,
        sizing=sizing,
        energia=energia,
        bateria=None,
    )

    _validar_resultado(
        finanzas,
        "Finanzas",
    )

    return finanzas


# ==========================================================
# LAYOUT
# ==========================================================

def _dimensiones_panel(sizing):

    panel = getattr(sizing, "panel", None)

    largo_panel_m = 2.20
    ancho_panel_m = 1.10

    if panel is None:
        return largo_panel_m, ancho_panel_m

    largo_mm = getattr(
        panel,
        "largo_mm",
        None,
    )

    ancho_mm = getattr(
        panel,
        "ancho_mm",
        None,
    )

    if largo_mm and ancho_mm:
        largo_panel_m = float(largo_mm) / 1000.0
        ancho_panel_m = float(ancho_mm) / 1000.0

    return largo_panel_m, ancho_panel_m


def _construir_layout(sizing):

    largo_panel_m, ancho_panel_m = (
        _dimensiones_panel(sizing)
    )

    return construir_layout_preliminar_fv(
        n_paneles=int(
            getattr(
                sizing,
                "n_paneles",
                0,
            )
            or 0
        ),
        largo_panel_m=largo_panel_m,
        ancho_panel_m=ancho_panel_m,
        factor_ocupacion=0.75,
        separacion_x_m=0.20,
        separacion_y_m=0.40,
        max_columnas=None,
    )


# ==========================================================
# RESULTADOS
# ==========================================================

def _resultado_final(
    *,
    sizing,
    paneles,
    energia,
    bateria,
    electrical,
    finanzas,
    layout_preliminar,
    optimizacion_economica,
):

    return ResultadoProyecto(
        sizing=sizing,
        paneles=paneles,
        strings=(
            paneles.strings
            if paneles
            else None
        ),
        energia=energia,
        bateria=bateria,
        electrical=electrical,
        financiero=finanzas,
        layout_preliminar=layout_preliminar,
        optimizacion_economica=(
            optimizacion_economica
        ),
        ok=True,
        errores=[],
    )


def _resultado_error(
    *,
    error,
    sizing,
    paneles,
    energia,
    bateria,
    electrical,
    finanzas,
    layout_preliminar,
    optimizacion_economica,
):

    print("💥 ERROR EN ORQUESTADOR:")
    print(traceback.format_exc())

    return ResultadoProyecto(
        sizing=sizing,
        paneles=paneles,
        strings=(
            paneles.strings
            if paneles
            else None
        ),
        energia=energia,
        bateria=bateria,
        electrical=electrical,
        financiero=finanzas,
        layout_preliminar=layout_preliminar,
        optimizacion_economica=(
            optimizacion_economica
        ),
        ok=False,
        errores=[str(error)],
    )


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================

def ejecutar_estudio(
    datos: Datosproyecto,
    deps: DependenciasEstudio,
) -> ResultadoProyecto:

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

        sizing = _ejecutar_sizing(
            datos,
            deps,
        )

        paneles = _ejecutar_paneles(
            datos,
            sizing,
            deps,
        )

        energia = _ejecutar_energia(
            datos,
            sizing,
            paneles,
            deps,
        )

        if _requiere_optimizacion(datos):
            (
                sizing,
                paneles,
                energia,
                optimizacion_economica,
            ) = _optimizar_y_recalcular(
                datos,
                sizing,
                energia,
                deps,
            )

        # Se ejecuta una sola vez sobre la energía definitiva.
        _aplicar_bateria_si_corresponde(
            datos,
            energia,
        )

        electrical = _ejecutar_electrical(
            datos,
            sizing,
            paneles,
            deps,
        )

        finanzas = _ejecutar_finanzas(
            datos,
            sizing,
            energia,
            deps,
        )

        bateria = _extraer_bateria_seleccionada(
            finanzas
        )

        layout_preliminar = _construir_layout(
            sizing
        )

        return _resultado_final(
            sizing=sizing,
            paneles=paneles,
            energia=energia,
            bateria=bateria,
            electrical=electrical,
            finanzas=finanzas,
            layout_preliminar=layout_preliminar,
            optimizacion_economica=(
                optimizacion_economica
            ),
        )

    except Exception as error:
        return _resultado_error(
            error=error,
            sizing=sizing,
            paneles=paneles,
            energia=energia,
            bateria=bateria,
            electrical=electrical,
            finanzas=finanzas,
            layout_preliminar=layout_preliminar,
            optimizacion_economica=(
                optimizacion_economica
            ),
        )
