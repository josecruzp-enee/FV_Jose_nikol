# -*- coding: utf-8 -*-
from __future__ import annotations

from energy.baterias.balance_bateria import (
    simular_balance_bateria_24h,
)
from energy.baterias.economia_bateria import (
    evaluar_escenario_bateria,
    seleccionar_mejor_escenario,
)
from energy.baterias.entrada_bateria import EntradaBateria
from energy.baterias.modelos import ConfigBateria
from energy.baterias.perfiles import (
    convertir_a_perfil_24h,
    preparar_perfiles_bateria,
)
from energy.baterias.recomendador_bateria import (
    generar_opciones_bateria,
)
from energy.baterias.resultado_bateria import (
    ResultadoSistemaBateria,
)


def _preparar_perfiles(
    entrada: EntradaBateria,
) -> dict:

    return preparar_perfiles_bateria(
        demanda_24h=entrada.demanda_24h_kwh,
        fv_24h=entrada.fv_horaria_kwh,
        consumo_anual_kwh=entrada.consumo_anual_kwh,
    )


def _crear_config(
    entrada: EntradaBateria,
    capacidad: float,
    potencia: float,
) -> ConfigBateria:

    return ConfigBateria(
        usar_bateria=True,
        capacidad_util_kwh=capacidad,
        potencia_max_kw=potencia,
        soc_inicial_pct=entrada.soc_inicial_pct,
        soc_min_pct=entrada.soc_min_pct,
        soc_max_pct=entrada.soc_max_pct,
        eficiencia_ida_vuelta=entrada.eficiencia_ida_vuelta,
        costo_usd_kwh=entrada.costo_bateria_usd_kwh,
        vida_util_anios=entrada.vida_util_bateria_anios,
    )


def _crear_escenario_base(
    entrada: EntradaBateria,
):

    return evaluar_escenario_bateria(
        entrada=entrada,
        nombre="Sin batería",
        capacidad_kwh=0.0,
        potencia_kw=0.0,
        resultado_tecnico=None,
    )


def _evaluar_opcion(
    *,
    entrada: EntradaBateria,
    perfiles: dict,
    opcion,
    escenario_base,
):

    config = _crear_config(
        entrada,
        opcion.capacidad_util_kwh,
        opcion.potencia_max_kw,
    )

    resultado = simular_balance_bateria_24h(
        demanda_24h_kwh=perfiles["demanda_24h"],
        fv_24h_kwh=perfiles["fv_24h"],
        cfg=config,
    )

    if not resultado.ok:
        return None

    return evaluar_escenario_bateria(
        entrada=entrada,
        nombre=(
            f"Batería "
            f"{opcion.capacidad_util_kwh:.0f} kWh"
        ),
        capacidad_kwh=opcion.capacidad_util_kwh,
        potencia_kw=opcion.potencia_max_kw,
        resultado_tecnico=resultado,
        energia_objetivo_kwh=opcion.energia_objetivo_kwh,
        escenario_base=escenario_base,
    )


def _generar_opciones(
    entrada: EntradaBateria,
    perfiles: dict,
):

    return generar_opciones_bateria(
        demanda_24h=perfiles["demanda_24h"],
        fv_24h=perfiles["fv_24h"],
        factor_aprovechamiento=(
            entrada.factor_aprovechamiento
        ),
        capacidades_comerciales_kwh=(
            entrada.capacidades_comerciales_kwh
        ),
    )


def _factor_normalizacion(
    entrada: EntradaBateria,
    perfiles: dict,
) -> tuple[float, float, float]:

    demanda_original = sum(
        convertir_a_perfil_24h(
            entrada.demanda_24h_kwh
        )
    )

    demanda_normalizada = sum(
        perfiles["demanda_24h"]
    )

    factor = (
        demanda_normalizada / demanda_original
        if demanda_original > 0
        else 1.0
    )

    return (
        demanda_original,
        demanda_normalizada,
        factor,
    )


def ejecutar_sistema_bateria(
    entrada: EntradaBateria,
) -> ResultadoSistemaBateria:

    errores = entrada.validar()

    if errores:
        return ResultadoSistemaBateria(
            ok=False,
            errores=errores,
        )

    perfiles = _preparar_perfiles(entrada)
    opciones = _generar_opciones(entrada, perfiles)

    escenario_base = _crear_escenario_base(
        entrada
    )

    escenarios = [escenario_base]

    for opcion in opciones:
        escenario = _evaluar_opcion(
            entrada=entrada,
            perfiles=perfiles,
            opcion=opcion,
            escenario_base=escenario_base,
        )

        if escenario:
            escenarios.append(escenario)

    if entrada.usar_bateria:
        seleccionado = seleccionar_mejor_escenario(
            escenarios=escenarios,
            vida_util_bateria_anios=(
                entrada.vida_util_bateria_anios
            ),
        )
    else:
        seleccionado = escenario_base

    original, normalizada, factor = (
        _factor_normalizacion(
            entrada,
            perfiles,
        )
    )

    referencia = opciones[-1] if opciones else None

    return ResultadoSistemaBateria(
        ok=True,
        consumo_anual_kwh=entrada.consumo_anual_kwh,
        demanda_diaria_original_kwh=original,
        demanda_diaria_normalizada_kwh=normalizada,
        factor_normalizacion_demanda=factor,
        excedente_fv_diario_kwh=(
            referencia.excedente_diario_kwh
            if referencia
            else 0.0
        ),
        consumo_nocturno_diario_kwh=(
            referencia.consumo_nocturno_kwh
            if referencia
            else 0.0
        ),
        energia_objetivo_diaria_kwh=(
            referencia.energia_objetivo_kwh
            if referencia
            else 0.0
        ),
        escenarios=escenarios,
        escenario_sin_bateria=escenario_base,
        escenario_seleccionado=seleccionado,
    )
