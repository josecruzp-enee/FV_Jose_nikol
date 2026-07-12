from __future__ import annotations

import traceback

from core.aplicacion.builder_paneles import construir_entrada_paneles
from core.aplicacion.dependencias import DependenciasEstudio
from core.dominio.contrato import ResultadoProyecto
from core.dominio.modelo import Datosproyecto
from core.servicios.layout import construir_layout_preliminar_fv
from core.servicios.optimizacion_fv import optimizar_kwp_doble_escenario
from energy.baterias import (
    construir_entrada_bateria,
    ejecutar_sistema_bateria,
)


def _validar_resultado(resultado, nombre: str) -> None:
    if resultado is None:
        raise ValueError(f"{nombre} devolvió None")

    if not getattr(resultado, "ok", True):
        errores = getattr(resultado, "errores", [f"Error en {nombre}"])
        raise ValueError(f"{nombre} inválido: {errores}")


# ==========================================================
# ETAPAS PRINCIPALES
# ==========================================================

def _ejecutar_sizing(datos, deps):
    resultado = deps.sizing.ejecutar(datos)
    _validar_resultado(resultado, "Sizing")
    return resultado


def _ejecutar_paneles(datos, sizing, deps):
    entrada = construir_entrada_paneles(datos, sizing)
    resultado = deps.paneles.ejecutar(entrada)
    _validar_resultado(resultado, "Paneles")
    return resultado


def _ejecutar_energia(datos, sizing, paneles, deps):
    resultado = deps.energia.ejecutar(datos, sizing, paneles)
    _validar_resultado(resultado, "Energía")
    return resultado


def _ejecutar_bateria(datos, sizing, energia):
    entrada = construir_entrada_bateria(
        datos=datos,
        sizing=sizing,
        energia=energia,
    )
    resultado = ejecutar_sistema_bateria(entrada)
    _validar_resultado(resultado, "Batería")
    return resultado


def _ejecutar_electrical(datos, sizing, paneles, deps):
    if deps.electrical is None:
        return None

    resultado = deps.electrical.ejecutar(
        datos=datos,
        paneles=paneles,
        sizing=sizing,
    )
    _validar_resultado(resultado, "Electrical")
    return resultado


def _ejecutar_finanzas(datos, sizing, energia, bateria, deps):
    if deps.finanzas is None:
        return None

    resultado = deps.finanzas.ejecutar(
        datos=datos,
        sizing=sizing,
        energia=energia,
        bateria=bateria,
    )
    _validar_resultado(resultado, "Finanzas")
    return resultado


# ==========================================================
# OPTIMIZACIÓN FV
# ==========================================================

def _requiere_optimizacion(datos) -> bool:
    sistema_fv = getattr(datos, "sistema_fv", {}) or {}
    return sistema_fv.get("modo") == "optimizacion_economica"


def _panel_w(sizing) -> float:
    panel = getattr(sizing, "panel", None)
    valor = float(getattr(panel, "pmax_w", 0.0) or 0.0)

    if valor <= 0:
        raise ValueError("Potencia de panel inválida para optimización.")

    return valor


def _costo_l_kwp(datos) -> float:
    costo_usd = float(getattr(datos, "costo_usd_kwp", 1200.0) or 1200.0)
    tcambio = float(getattr(datos, "tcambio", 26.61) or 26.61)
    return costo_usd * tcambio


def _calcular_optimizacion(datos, sizing, energia):
    demanda = getattr(datos, "consumo_horario_24h_kwh", {}) or {}
    energia_horaria = getattr(energia, "energia_horaria_kwh", None)

    if not demanda:
        raise ValueError("Optimización requiere perfil horario de consumo.")
    if not energia_horaria:
        raise ValueError("Optimización requiere energía horaria.")

    return optimizar_kwp_doble_escenario(
        demanda_24h=demanda,
        energia_horaria_base_kwh=energia_horaria,
        pdc_kw_base=float(sizing.pdc_kw),
        panel_w=_panel_w(sizing),
        tarifa_compra_l_kwh=float(
            getattr(datos, "tarifa_energia", 0.0) or 0.0
        ),
        precio_inyeccion_l_kwh=2.20,
        costo_l_kwp=_costo_l_kwp(datos),
        tasa_descuento_anual=float(
            getattr(datos, "tasa_anual", 0.10) or 0.10
        ),
        vida_util_anios=20,
        kwp_min=1.0,
        kwp_max=500.0,
        paso_kwp=1.0,
    )


def _aplicar_optimizacion(datos, optimizacion) -> None:
    escenario = optimizacion["sin_inyeccion"]
    sistema_fv = datos.sistema_fv

    sistema_fv["modo_original"] = "optimizacion_economica"
    sistema_fv["modo"] = "kw_objetivo"
    sistema_fv["valor"] = float(escenario["pdc_kw"])
    sistema_fv["optimizacion_economica"] = optimizacion


def _optimizar_y_recalcular(datos, sizing, energia, deps):
    optimizacion = _calcular_optimizacion(datos, sizing, energia)
    _aplicar_optimizacion(datos, optimizacion)

    sizing = _ejecutar_sizing(datos, deps)
    paneles = _ejecutar_paneles(datos, sizing, deps)
    energia = _ejecutar_energia(datos, sizing, paneles, deps)

    return sizing, paneles, energia, optimizacion


# ==========================================================
# LAYOUT
# ==========================================================

def _dimensiones_panel(sizing):
    panel = getattr(sizing, "panel", None)
    largo_mm = getattr(panel, "largo_mm", None)
    ancho_mm = getattr(panel, "ancho_mm", None)

    if largo_mm and ancho_mm:
        return float(largo_mm) / 1000.0, float(ancho_mm) / 1000.0

    return 2.20, 1.10


def _construir_layout(sizing):
    largo, ancho = _dimensiones_panel(sizing)

    return construir_layout_preliminar_fv(
        n_paneles=int(getattr(sizing, "n_paneles", 0) or 0),
        largo_panel_m=largo,
        ancho_panel_m=ancho,
        factor_ocupacion=0.75,
        separacion_x_m=0.20,
        separacion_y_m=0.40,
        max_columnas=None,
    )


# ==========================================================
# RESULTADOS
# ==========================================================

def _crear_resultado(
    *,
    ok,
    error=None,
    sizing=None,
    paneles=None,
    energia=None,
    bateria=None,
    electrical=None,
    finanzas=None,
    layout=None,
    optimizacion=None,
):
    return ResultadoProyecto(
        sizing=sizing,
        paneles=paneles,
        strings=getattr(paneles, "strings", None),
        energia=energia,
        bateria=bateria,
        electrical=electrical,
        financiero=finanzas,
        layout_preliminar=layout,
        optimizacion_economica=optimizacion,
        ok=ok,
        errores=[] if ok else [str(error)],
    )


def _estado_inicial() -> dict:
    return {
        "sizing": None,
        "paneles": None,
        "energia": None,
        "bateria": None,
        "electrical": None,
        "finanzas": None,
        "layout": None,
        "optimizacion": None,
    }


def _ejecutar_base(datos, deps, estado) -> None:
    estado["sizing"] = _ejecutar_sizing(datos, deps)
    estado["paneles"] = _ejecutar_paneles(
        datos, estado["sizing"], deps
    )
    estado["energia"] = _ejecutar_energia(
        datos, estado["sizing"], estado["paneles"], deps
    )


def _optimizar_si_corresponde(datos, deps, estado) -> None:
    if not _requiere_optimizacion(datos):
        return

    resultado = _optimizar_y_recalcular(
        datos,
        estado["sizing"],
        estado["energia"],
        deps,
    )
    claves = ("sizing", "paneles", "energia", "optimizacion")
    estado.update(dict(zip(claves, resultado)))


def _completar_estudio(datos, deps, estado) -> None:
    estado["bateria"] = _ejecutar_bateria(
        datos, estado["sizing"], estado["energia"]
    )
    estado["electrical"] = _ejecutar_electrical(
        datos, estado["sizing"], estado["paneles"], deps
    )
    estado["finanzas"] = _ejecutar_finanzas(
        datos,
        estado["sizing"],
        estado["energia"],
        estado["bateria"],
        deps,
    )
    estado["layout"] = _construir_layout(estado["sizing"])


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================

def ejecutar_estudio(
    datos: Datosproyecto,
    deps: DependenciasEstudio,
) -> ResultadoProyecto:
    estado = _estado_inicial()

    try:
        datos.validar_minimo()
        _ejecutar_base(datos, deps, estado)
        _optimizar_si_corresponde(datos, deps, estado)
        _completar_estudio(datos, deps, estado)
        return _crear_resultado(ok=True, **estado)

    except Exception as error:
        print("💥 ERROR EN ORQUESTADOR:")
        print(traceback.format_exc())
        return _crear_resultado(ok=False, error=error, **estado)
